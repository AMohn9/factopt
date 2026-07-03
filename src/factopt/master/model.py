"""CP-SAT master problem: macro placement + orientation + coarse routing.

Places every macro of a :class:`~factopt.macros.library.MacroProblem` on an
integer tile grid with pairwise no-overlap (inflated by a routing margin),
chooses a quarter-turn **orientation** per macro (edge-pinned I/O macros stay
in their authored orientation), honors west/east edge pins, and optimizes
lexicographically via two solves:

1. bounding-box area (optionally relaxed by ``area_slack``),
2. flow-weighted HPWL of each net's pins -- source port plus every sink
   port -- (+ coarse congestion when coarse routing is enabled).

Benders-style cuts (:mod:`factopt.master.cuts`) are applied to the model
before solving, so detailed-routing failures constrain future placements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from factopt.macros.cell import _SIDE_VEC, MacroCell, PlacedMacro, rotated
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
    # Orientation: per macro, the 4 rotated cell variants, one bool per
    # variant (exactly one true), an index channel, and w/h as IntVars.
    cells: dict[str, list[MacroCell]] = field(default_factory=dict)
    orient: dict[str, list[cp_model.IntVar]] = field(default_factory=dict)
    o_idx: dict[str, cp_model.IntVar] = field(default_factory=dict)
    w: dict[str, cp_model.IntVar] = field(default_factory=dict)
    h: dict[str, cp_model.IntVar] = field(default_factory=dict)
    # Reversible input lanes: per (macro, port) a bool "use the reverse end",
    # and its AND with each orientation bool (reversal is orthogonal to the
    # quarter-turn, so the port tile depends on both).
    rev: dict[tuple[str, str], cp_model.IntVar] = field(default_factory=dict)
    rev_orient: dict[tuple[str, str, int], cp_model.IntVar] = field(default_factory=dict)

    def _port_terms(self, macro_id: str, port_id: str, access: bool):
        """Linear (x, y) expressions of a port's tile (``access=False``) or its
        access tile (``access=True``), summed over the orientation choice and,
        for reversible ports, the reverse-end choice."""
        ob = self.orient[macro_id]
        reversible = (macro_id, port_id) in self.rev
        tx, ty = [], []
        for k in range(4):
            p = self.cells[macro_id][k].port(port_id)
            prim = p.primary_end
            bx, by = prim.local_position
            if access:
                dx, dy = _SIDE_VEC[prim.side]
                bx, by = bx + dx, by + dy
            tx.append(ob[k] * bx)
            ty.append(ob[k] * by)
            if reversible and p.reverse is not None:
                aux = self.rev_orient[(macro_id, port_id, k)]
                rx, ry = p.reverse.local_position
                if access:
                    dx, dy = _SIDE_VEC[p.reverse.side]
                    rx, ry = rx + dx, ry + dy
                tx.append(aux * (rx - bx))
                ty.append(aux * (ry - by))
        return self.x[macro_id] + sum(tx), self.y[macro_id] + sum(ty)

    def port_exprs(self, macro_id: str, port_id: str):
        """(x, y) linear expressions of a port's tile under the chosen
        orientation and reverse-end choice."""
        return self._port_terms(macro_id, port_id, access=False)

    def port_access_exprs(self, macro_id: str, port_id: str):
        """(x, y) linear expressions of a port's access tile (just outside
        the footprint) under the chosen orientation and reverse-end choice."""
        return self._port_terms(macro_id, port_id, access=True)


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

    max_dim = max(max_w, max_h)
    x = {mid: model.new_int_var(0, max_w, f"x_{mid}") for mid in macros}
    y = {mid: model.new_int_var(0, max_h, f"y_{mid}") for mid in macros}
    bbox_w = model.new_int_var(1, max_w, "bbox_w")
    bbox_h = model.new_int_var(1, max_h, "bbox_h")

    # Orientation: 4 rotated variants per macro; edge-pinned I/O macros keep
    # their authored orientation (their contract is a fixed boundary side).
    cells: dict[str, list[MacroCell]] = {}
    orient: dict[str, list[cp_model.IntVar]] = {}
    o_idx: dict[str, cp_model.IntVar] = {}
    w: dict[str, cp_model.IntVar] = {}
    h: dict[str, cp_model.IntVar] = {}
    for mid, m in macros.items():
        cells[mid] = [rotated(m, k) for k in range(4)]
        ob = [model.new_bool_var(f"o_{mid}_{k}") for k in range(4)]
        model.add_exactly_one(ob)
        oi = model.new_int_var(0, 3, f"oi_{mid}")
        model.add(oi == sum(k * ob[k] for k in range(4)))
        if mid in problem.pins:
            model.add(oi == 0)
        wm = model.new_int_var(1, max_dim, f"w_{mid}")
        hm = model.new_int_var(1, max_dim, f"h_{mid}")
        model.add(wm == sum(ob[k] * cells[mid][k].width for k in range(4)))
        model.add(hm == sum(ob[k] * cells[mid][k].height for k in range(4)))
        orient[mid], o_idx[mid], w[mid], h[mid] = ob, oi, wm, hm

    # Reversible input lanes: a bool per (macro, port) picking the reverse end,
    # plus its AND with each orientation bool (the port tile depends on both).
    rev: dict[tuple[str, str], cp_model.IntVar] = {}
    rev_orient: dict[tuple[str, str, int], cp_model.IntVar] = {}
    for mid, m in macros.items():
        for p in m.ports:
            if not p.reversible:
                continue
            rp = model.new_bool_var(f"rev_{mid}_{p.id}")
            rev[(mid, p.id)] = rp
            for k in range(4):
                aux = model.new_bool_var(f"revor_{mid}_{p.id}_{k}")
                model.add_multiplication_equality(aux, [orient[mid][k], rp])
                rev_orient[(mid, p.id, k)] = aux

    # No-overlap with a `margin`-tile separation: inflate each rectangle.
    xi, yi = [], []
    for mid in macros:
        xe = model.new_int_var(0, max_w + max_dim + margin, f"xe_{mid}")
        ye = model.new_int_var(0, max_h + max_dim + margin, f"ye_{mid}")
        model.add(xe == x[mid] + w[mid] + margin)
        model.add(ye == y[mid] + h[mid] + margin)
        xi.append(model.new_interval_var(x[mid], w[mid] + margin, xe, f"xi_{mid}"))
        yi.append(model.new_interval_var(y[mid], h[mid] + margin, ye, f"yi_{mid}"))
    model.add_no_overlap_2d(xi, yi)

    # Inside the bounding box.
    for mid in macros:
        model.add(x[mid] + w[mid] <= bbox_w)
        model.add(y[mid] + h[mid] <= bbox_h)

    # Port clearance: a port's access tile must stay inside the bounding box
    # with one extra tile beyond it, so a route can approach the mouth from
    # the side instead of only straight down a 1-wide dead-end corridor.
    # Sides depend on the chosen orientation, so guard per variant.
    for mid, m in macros.items():
        pinned = problem.pins.get(mid)
        for k in range(4):
            # A reversible port may sit on either end, so reserve clearance
            # for both realizations regardless of which the solver picks.
            sides: set = set()
            for p in cells[mid][k].ports:
                sides.add(p.side)
                if p.reverse is not None:
                    sides.add(p.reverse.side)
            ck = cells[mid][k]
            if "west" in sides and pinned != "west":
                model.add(x[mid] >= 2).only_enforce_if(orient[mid][k])
            if "east" in sides and pinned != "east":
                model.add(x[mid] + ck.width + 2 <= bbox_w).only_enforce_if(orient[mid][k])
            if "north" in sides and pinned != "north":
                model.add(y[mid] >= 2).only_enforce_if(orient[mid][k])
            if "south" in sides and pinned != "south":
                model.add(y[mid] + ck.height + 2 <= bbox_h).only_enforce_if(orient[mid][k])

    # Edge pins: west-pinned macros hug x=0, east-pinned hug the east edge.
    for mid, side in problem.pins.items():
        if side == "west":
            model.add(x[mid] == 0)
        elif side == "east":
            model.add(x[mid] + w[mid] == bbox_w)
        elif side == "north":
            model.add(y[mid] == 0)
        elif side == "south":
            model.add(y[mid] + h[mid] == bbox_h)

    return MasterVars(
        model=model,
        x=x,
        y=y,
        bbox_w=bbox_w,
        bbox_h=bbox_h,
        max_w=max_w,
        max_h=max_h,
        cells=cells,
        orient=orient,
        o_idx=o_idx,
        w=w,
        h=h,
        rev=rev,
        rev_orient=rev_orient,
    )


def _net_weight(rate_per_sec: float) -> int:
    return max(1, round(rate_per_sec * RATE_SCALE))


def _net_pins(net) -> list[tuple[str, str]]:
    """(macro, port) of every pin of a net: the source plus each sink."""
    return [(net.source_macro, net.source_port)] + [(s.macro, s.port) for s in net.sinks]


def _flow_distance_expr(problem: MacroProblem, v: MasterVars):
    """Sum over nets of scaled_rate * HPWL(pins).

    HPWL (half-perimeter wire length of the pins' bounding box) is the
    standard placement proxy for a multi-sink net's Steiner-tree length:
    exact for 2-3 pins, a lower bound beyond. For a 2-pin net it reduces to
    the old source-sink Manhattan distance.
    """
    model = v.model
    terms = []
    for net in problem.nets:
        xs, ys = [], []
        for macro_id, port_id in _net_pins(net):
            px, py = v.port_exprs(macro_id, port_id)
            xs.append(px)
            ys.append(py)
        parts = []
        for tag, exprs, hi in (("x", xs, v.max_w), ("y", ys, v.max_h)):
            lo_v = model.new_int_var(0, hi, f"{tag}min_{net.id}")
            hi_v = model.new_int_var(0, hi, f"{tag}max_{net.id}")
            model.add_min_equality(lo_v, exprs)
            model.add_max_equality(hi_v, exprs)
            parts.append(hi_v - lo_v)
        terms.append(_net_weight(net.rate_per_sec) * sum(parts))
    return sum(terms)


def flow_distance(problem: MacroProblem, placements: dict[str, PlacedMacro]) -> int:
    """Rate-weighted HPWL of a concrete placement."""
    total = 0
    for net in problem.nets:
        xs, ys = [], []
        for macro_id, port_id in _net_pins(net):
            pm = placements[macro_id]
            px, py = pm.port_tile(pm.cell.port(port_id))
            xs.append(px)
            ys.append(py)
        hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
        total += _net_weight(net.rate_per_sec) * hpwl
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
    max_area: int | None = None,
) -> MasterSolution:
    """Solve placement (and coarse routing when ``coarse_cell`` is set).

    ``area_slack`` relaxes the stage-1 optimal area by that fraction before
    minimizing flow distance, trading footprint for shorter routes.
    ``max_area``, if given, is a hard bounding-box cap (both stages) -- the
    loop uses it as an incumbent bound so later iterations only look for
    strictly tighter placements.
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
    if max_area is not None:
        model.add(area <= max_area)
    model.minimize(area)
    s1, st1 = _solve(model, time_limit_s, workers)
    if st1 not in ("OPTIMAL", "FEASIBLE"):
        return MasterSolution(status=st1)
    best_area = s1.value(area)

    # Stage 2: bound area, minimize flow-weighted distance (+ congestion).
    model.clear_objective()
    slack_area = int(best_area * (1.0 + area_slack))
    if max_area is not None:
        slack_area = min(slack_area, max_area)
    model.add(area <= slack_area)
    objective = _flow_distance_expr(problem, v)
    if coarse_vars is not None:
        objective = objective + coarse_vars.congestion_expr()
    model.minimize(objective)
    s2, st2 = _solve(model, time_limit_s, workers)
    if st2 not in ("OPTIMAL", "FEASIBLE"):
        s2, st2 = s1, st1  # tight time limits can starve stage 2; keep stage 1

    placements = {}
    for mid in problem.macros:
        k = s2.value(v.o_idx[mid])
        port_choice = {
            pid: bool(s2.value(rp))
            for (m, pid), rp in v.rev.items()
            if m == mid
        }
        placements[mid] = PlacedMacro(
            cell=v.cells[mid][k],
            x=s2.value(v.x[mid]),
            y=s2.value(v.y[mid]),
            orientation=k,
            port_choice=port_choice,
        )
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
