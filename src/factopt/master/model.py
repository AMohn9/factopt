"""CP-SAT master problem: macro placement (M2) + optional coarse routing (M3).

Places every macro of a :class:`~factopt.macros.library.MacroProblem` on an
integer tile grid with pairwise no-overlap (inflated by a routing margin),
honors west/east edge pins, and optimizes lexicographically via two solves:

1. bounding-box area (optionally relaxed by ``area_slack``),
2. flow-weighted Manhattan distance between each net's ports
   (+ coarse congestion when coarse routing is enabled).

Benders-style cuts (:mod:`factopt.master.cuts`) are applied to the model
before solving, so detailed-routing failures constrain future placements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from factopt.macros.cell import PlacedMacro
from factopt.macros.library import MacroProblem

if TYPE_CHECKING:
    from factopt.master.coarse import CoarseSolution
    from factopt.master.cuts import BendersCut

# Scaled integer flow units: 1 unit = 1/RATE_SCALE items/s.
RATE_SCALE = 100


@dataclass
class MasterSolution:
    status: str  # CP-SAT status name, e.g. "OPTIMAL" | "FEASIBLE" | "INFEASIBLE"
    placements: dict[str, PlacedMacro] = field(default_factory=dict)
    width: int = 0
    height: int = 0
    flow_distance: int = 0  # rate-weighted tiles, in RATE_SCALE units
    coarse: "CoarseSolution | None" = None

    @property
    def ok(self) -> bool:
        return self.status in ("OPTIMAL", "FEASIBLE")

    @property
    def area(self) -> int:
        return self.width * self.height

    def port_tile(self, macro_id: str, port_id: str) -> tuple[int, int]:
        pm = self.placements[macro_id]
        return pm.port_tile(pm.cell.port(port_id))

    def port_access_tile(self, macro_id: str, port_id: str) -> tuple[int, int]:
        pm = self.placements[macro_id]
        return pm.port_access_tile(pm.cell.port(port_id))


@dataclass
class MasterVars:
    """Model variables shared between the placement builder and extensions
    (coarse routing, cuts)."""

    model: cp_model.CpModel
    x: dict[str, cp_model.IntVar]
    y: dict[str, cp_model.IntVar]
    bbox_w: cp_model.IntVar
    bbox_h: cp_model.IntVar
    max_w: int
    max_h: int


def default_bounds(problem: MacroProblem, margin: int) -> tuple[int, int]:
    """A square canvas comfortably larger than the total macro area."""
    total = sum((m.width + margin) * (m.height + margin) for m in problem.macros.values())
    side = math.ceil(1.6 * math.sqrt(total))
    side = max(
        side,
        max(m.width for m in problem.macros.values()) + 2 * margin,
        max(m.height for m in problem.macros.values()) + 2 * margin,
    )
    return side, side


def _build_placement(
    problem: MacroProblem, margin: int, max_w: int | None, max_h: int | None
) -> MasterVars:
    model = cp_model.CpModel()
    macros = problem.macros

    if max_w is None or max_h is None:
        dw, dh = default_bounds(problem, margin)
        max_w = max_w if max_w is not None else dw
        max_h = max_h if max_h is not None else dh

    x = {mid: model.new_int_var(0, max_w - m.width, f"x_{mid}") for mid, m in macros.items()}
    y = {mid: model.new_int_var(0, max_h - m.height, f"y_{mid}") for mid, m in macros.items()}
    bbox_w = model.new_int_var(1, max_w, "bbox_w")
    bbox_h = model.new_int_var(1, max_h, "bbox_h")

    # No-overlap with a `margin`-tile separation: inflate each rectangle.
    xi, yi = [], []
    for mid, m in macros.items():
        xi.append(model.new_fixed_size_interval_var(x[mid], m.width + margin, f"xi_{mid}"))
        yi.append(model.new_fixed_size_interval_var(y[mid], m.height + margin, f"yi_{mid}"))
    model.add_no_overlap_2d(xi, yi)

    # Inside the bounding box.
    for mid, m in macros.items():
        model.add(x[mid] + m.width <= bbox_w)
        model.add(y[mid] + m.height <= bbox_h)

    # Port clearance: every port's access tile must stay inside the bounding
    # box (a west port one tile from x=0 would be unreachable).
    for mid, m in macros.items():
        pinned = problem.pins.get(mid)
        sides = {p.side for p in m.ports}
        if "west" in sides and pinned != "west":
            model.add(x[mid] >= 1)
        if "east" in sides and pinned != "east":
            model.add(x[mid] + m.width + 1 <= bbox_w)
        if "north" in sides and pinned != "north":
            model.add(y[mid] >= 1)
        if "south" in sides and pinned != "south":
            model.add(y[mid] + m.height + 1 <= bbox_h)

    # Edge pins: west-pinned macros hug x=0, east-pinned hug the east edge.
    for mid, side in problem.pins.items():
        if side == "west":
            model.add(x[mid] == 0)
        elif side == "east":
            model.add(x[mid] + macros[mid].width == bbox_w)
        elif side == "north":
            model.add(y[mid] == 0)
        elif side == "south":
            model.add(y[mid] + macros[mid].height == bbox_h)

    return MasterVars(
        model=model, x=x, y=y, bbox_w=bbox_w, bbox_h=bbox_h, max_w=max_w, max_h=max_h
    )


def _net_weight(rate_per_sec: float) -> int:
    return max(1, round(rate_per_sec * RATE_SCALE))


def _flow_distance_expr(problem: MacroProblem, v: MasterVars):
    """Sum over nets of scaled_rate * manhattan(source_port, sink_port)."""
    model = v.model
    terms = []
    span = v.max_w + v.max_h
    for net in problem.nets:
        sp = problem.macros[net.source_macro].port(net.source_port).local_position
        dp = problem.macros[net.sink_macro].port(net.sink_port).local_position
        sx = v.x[net.source_macro] + sp[0]
        sy = v.y[net.source_macro] + sp[1]
        tx = v.x[net.sink_macro] + dp[0]
        ty = v.y[net.sink_macro] + dp[1]
        ax = model.new_int_var(0, span, f"ax_{net.id}")
        ay = model.new_int_var(0, span, f"ay_{net.id}")
        model.add_abs_equality(ax, sx - tx)
        model.add_abs_equality(ay, sy - ty)
        terms.append(_net_weight(net.rate_per_sec) * (ax + ay))
    return sum(terms)


def flow_distance(problem: MacroProblem, placements: dict[str, PlacedMacro]) -> int:
    """Rate-weighted Manhattan port distance of a concrete placement."""
    total = 0
    for net in problem.nets:
        src = placements[net.source_macro]
        dst = placements[net.sink_macro]
        sx, sy = src.port_tile(src.cell.port(net.source_port))
        tx, ty = dst.port_tile(dst.cell.port(net.sink_port))
        total += _net_weight(net.rate_per_sec) * (abs(sx - tx) + abs(sy - ty))
    return total


def _solve(
    model: cp_model.CpModel, time_limit_s: float, workers: int
) -> tuple[cp_model.CpSolver, str]:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_workers = workers
    status = solver.solve(model)
    return solver, solver.status_name(status)


def solve_master(
    problem: MacroProblem,
    cuts: "list[BendersCut] | None" = None,
    margin: int = 1,
    max_w: int | None = None,
    max_h: int | None = None,
    area_slack: float = 0.0,
    coarse_cell: int | None = None,
    time_limit_s: float = 20.0,
    workers: int = 8,
) -> MasterSolution:
    """Solve placement (and coarse routing when ``coarse_cell`` is set).

    ``area_slack`` relaxes the stage-1 optimal area by that fraction before
    minimizing flow distance, trading footprint for shorter routes.
    """
    v = _build_placement(problem, margin, max_w, max_h)
    model = v.model

    coarse_vars = None
    if coarse_cell is not None:
        from factopt.master.coarse import add_coarse_routing

        coarse_vars = add_coarse_routing(problem, v, cell=coarse_cell)

    if cuts:
        from factopt.master.cuts import apply_cuts

        apply_cuts(cuts, problem, v, coarse_vars)

    # Stage 1: minimize bounding-box area.
    area = model.new_int_var(1, v.max_w * v.max_h, "area")
    model.add_multiplication_equality(area, [v.bbox_w, v.bbox_h])
    model.minimize(area)
    s1, st1 = _solve(model, time_limit_s, workers)
    if st1 not in ("OPTIMAL", "FEASIBLE"):
        return MasterSolution(status=st1)
    best_area = s1.value(area)

    # Stage 2: bound area, minimize flow-weighted distance (+ congestion).
    model.clear_objective()
    model.add(area <= int(best_area * (1.0 + area_slack)))
    objective = _flow_distance_expr(problem, v)
    if coarse_vars is not None:
        objective = objective + coarse_vars.congestion_expr()
    model.minimize(objective)
    s2, st2 = _solve(model, time_limit_s, workers)
    if st2 not in ("OPTIMAL", "FEASIBLE"):
        s2, st2 = s1, st1  # tight time limits can starve stage 2; keep stage 1

    placements = {
        mid: PlacedMacro(cell=m, x=s2.value(v.x[mid]), y=s2.value(v.y[mid]))
        for mid, m in problem.macros.items()
    }
    sol = MasterSolution(
        status=st2,
        placements=placements,
        width=s2.value(v.bbox_w),
        height=s2.value(v.bbox_h),
        flow_distance=flow_distance(problem, placements),
    )
    if coarse_vars is not None:
        from factopt.master.coarse import extract_coarse

        sol.coarse = extract_coarse(coarse_vars, s2)
    return sol
