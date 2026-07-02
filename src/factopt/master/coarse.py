"""Coarse routing extension for the master problem (M3).

Overlays a grid of ``cell`` x ``cell`` tile bins on the placement canvas and
routes every net as a **Steiner flow** over the coarse cells: the source cell
supplies one unit per sink, each sink cell consumes one, and an arc is
*used* by the net when any amount flows over it. Congestion and tree length
count used arcs (a belt crosses a boundary once no matter how many sinks sit
downstream), which is the coarse mirror of the detailed router's shared-trunk
trees. Arc capacity across each cell boundary shrinks when macros span the
boundary, so the master avoids placements whose flows would have to squeeze
through walls.

The capacity model is deliberately *optimistic* (a macro only blocks a
boundary row when it covers both sides), because an optimistic master can be
corrected by Benders cuts from the detailed router, while a pessimistic one
rules out feasible layouts forever.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from factopt.macros.library import MacroProblem
from factopt.master.model import MasterVars

Cell = tuple[int, int]  # (i, j) coarse coordinates
Arc = tuple[Cell, Cell]  # directed
Edge = tuple[Cell, Cell]  # undirected, canonical order (c1 < c2)

# Objective weights (must be comparable to flow-distance units:
# RATE_SCALE * tiles, ~100 per tile of a 1 item/s net).
SATURATION_WEIGHT = 500  # per boundary at >= full utilization
COARSE_LENGTH_WEIGHT = 2  # per net per arc used


@dataclass
class CoarseVars:
    cell: int
    cols: int
    rows: int
    # Per (net, arc): integer flow 0..n_sinks and a bool "this net uses the arc".
    flow: dict[tuple[str, Arc], cp_model.IntVar]
    arc_used: dict[tuple[str, Arc], cp_model.IntVar]
    cap: dict[Edge, cp_model.IntVar]
    used: dict[Edge, cp_model.IntVar]
    saturated: dict[Edge, cp_model.IntVar]
    src_cell: dict[str, tuple[cp_model.IntVar, cp_model.IntVar]]
    snk_cell: dict[tuple[str, int], tuple[cp_model.IntVar, cp_model.IntVar]]
    v: MasterVars

    def congestion_expr(self):
        # Tree length = arcs used (shared trunk edges count once per net).
        return SATURATION_WEIGHT * sum(self.saturated.values()) + COARSE_LENGTH_WEIGHT * sum(
            self.arc_used.values()
        )


@dataclass
class CoarseSolution:
    cell: int
    cols: int
    rows: int
    routes: dict[str, list[Arc]] = field(default_factory=dict)
    utilization: dict[Edge, tuple[int, int]] = field(default_factory=dict)  # used, cap

    @property
    def max_utilization(self) -> float:
        worst = 0.0
        for used, cap in self.utilization.values():
            if used:
                worst = max(worst, used / cap if cap else float("inf"))
        return worst


def _edges(cols: int, rows: int) -> list[Edge]:
    out: list[Edge] = []
    for i in range(cols):
        for j in range(rows):
            if i + 1 < cols:
                out.append((((i, j)), (i + 1, j)))
            if j + 1 < rows:
                out.append((((i, j)), (i, j + 1)))
    return out


def _cell_bools(
    model: cp_model.CpModel,
    ci: cp_model.IntVar,
    cj: cp_model.IntVar,
    cols: int,
    rows: int,
    tag: str,
) -> dict[Cell, cp_model.IntVar]:
    """b[c] <=> (ci, cj) == c, via per-axis indicator channels."""
    bi = [model.new_bool_var(f"{tag}_i{i}") for i in range(cols)]
    bj = [model.new_bool_var(f"{tag}_j{j}") for j in range(rows)]
    model.add_map_domain(ci, bi)
    model.add_map_domain(cj, bj)
    out: dict[Cell, cp_model.IntVar] = {}
    for i in range(cols):
        for j in range(rows):
            b = model.new_bool_var(f"{tag}_c{i}_{j}")
            model.add_multiplication_equality(b, [bi[i], bj[j]])
            out[(i, j)] = b
    return out


def add_coarse_routing(problem: MacroProblem, v: MasterVars, cell: int = 4) -> CoarseVars:
    model = v.model
    cols = -(-v.max_w // cell)
    rows = -(-v.max_h // cell)
    edges = _edges(cols, rows)

    # -- boundary capacities from macro coverage ---------------------------
    # A macro blocks a boundary row/column where it covers BOTH adjacent
    # tiles (it spans the boundary); crossings along its wall stay open.
    cap: dict[Edge, cp_model.IntVar] = {}
    for c1, c2 in edges:
        blocked_terms = []
        vertical = c1[0] != c2[0]  # boundary crossed by horizontal movement
        if vertical:
            bx = c2[0] * cell  # first tile column of c2
            r0, r1 = c1[1] * cell, (c1[1] + 1) * cell
        else:
            by = c2[1] * cell
            r0, r1 = c1[0] * cell, (c1[0] + 1) * cell

        for mid in problem.macros:
            if vertical:
                pos, span = v.x[mid], v.w[mid]
                perp, perp_span = v.y[mid], v.h[mid]
                b = bx
            else:
                pos, span = v.y[mid], v.h[mid]
                perp, perp_span = v.x[mid], v.w[mid]
                b = by
            tag = f"blk_{mid}_{c1}_{c2}"
            # spans == (pos <= b-1 AND pos+span >= b+1), via two half reifications.
            spans = model.new_bool_var(f"{tag}_spans")
            lo = model.new_bool_var(f"{tag}_lo")
            hi = model.new_bool_var(f"{tag}_hi")
            model.add(pos <= b - 1).only_enforce_if(lo)
            model.add(pos >= b).only_enforce_if(lo.negated())
            model.add(pos + span >= b + 1).only_enforce_if(hi)
            model.add(pos + span <= b).only_enforce_if(hi.negated())
            model.add_multiplication_equality(spans, [lo, hi])

            # Overlap of the macro with the boundary's row/column range.
            max_dim = max(v.max_w, v.max_h)
            lo_e = model.new_int_var(0, max_dim, f"{tag}_l")
            hi_e = model.new_int_var(0, 2 * max_dim, f"{tag}_h")
            model.add_max_equality(lo_e, [perp, r0])
            model.add_min_equality(hi_e, [perp + perp_span, r1])
            ov = model.new_int_var(0, cell, f"{tag}_ov")
            model.add_max_equality(ov, [hi_e - lo_e, 0])

            blk = model.new_int_var(0, cell, f"{tag}_blk")
            model.add_multiplication_equality(blk, [spans, ov])
            blocked_terms.append(blk)

        c = model.new_int_var(0, cell, f"cap_{c1}_{c2}")
        model.add_max_equality(c, [cell - sum(blocked_terms), 0])
        cap[(c1, c2)] = c

    # -- cells at least partially inside the bounding box ------------------
    inbox: dict[Cell, cp_model.IntVar] = {}
    for i in range(cols):
        for j in range(rows):
            b = model.new_bool_var(f"inbox_{i}_{j}")
            model.add(v.bbox_w >= i * cell + 1).only_enforce_if(b)
            model.add(v.bbox_h >= j * cell + 1).only_enforce_if(b)
            bx_ = model.new_bool_var(f"inbox_{i}_{j}_x")
            model.add(v.bbox_w >= i * cell + 1).only_enforce_if(bx_)
            model.add(v.bbox_w <= i * cell).only_enforce_if(bx_.negated())
            by_ = model.new_bool_var(f"inbox_{i}_{j}_y")
            model.add(v.bbox_h >= j * cell + 1).only_enforce_if(by_)
            model.add(v.bbox_h <= j * cell).only_enforce_if(by_.negated())
            model.add_multiplication_equality(b, [bx_, by_])
            inbox[(i, j)] = b

    # -- Steiner flows per net ----------------------------------------------
    # Source supplies one unit per sink; each sink consumes one. ``arc_used``
    # reifies "any flow on this arc", which is what shares capacity and what
    # the congestion/length objective counts (a trunk belt crosses a boundary
    # once regardless of how many sinks it feeds).
    flow: dict[tuple[str, Arc], cp_model.IntVar] = {}
    arc_used: dict[tuple[str, Arc], cp_model.IntVar] = {}
    src_cell: dict[str, tuple[cp_model.IntVar, cp_model.IntVar]] = {}
    snk_cell: dict[tuple[str, int], tuple[cp_model.IntVar, cp_model.IntVar]] = {}

    for net in problem.nets:
        k = len(net.sinks)
        arcs: list[Arc] = []
        for c1, c2 in edges:
            arcs.append((c1, c2))
            arcs.append((c2, c1))
        for a in arcs:
            f = model.new_int_var(0, k, f"f_{net.id}_{a}")
            u = model.new_bool_var(f"fu_{net.id}_{a}")
            model.add(f <= k * u)
            model.add(u <= f)
            model.add(u <= inbox[a[0]])
            model.add(u <= inbox[a[1]])
            flow[(net.id, a)] = f
            arc_used[(net.id, a)] = u

        # Coarse cell of each pin port, as a function of placement and
        # orientation.
        def _port_cell(macro_id: str, port_id: str, tag: str):
            px_expr, py_expr = v.port_exprs(macro_id, port_id)
            px = model.new_int_var(0, v.max_w, f"{tag}_px")
            py = model.new_int_var(0, v.max_h, f"{tag}_py")
            model.add(px == px_expr)
            model.add(py == py_expr)
            ci = model.new_int_var(0, cols - 1, f"{tag}_ci")
            cj = model.new_int_var(0, rows - 1, f"{tag}_cj")
            model.add_division_equality(ci, px, cell)
            model.add_division_equality(cj, py, cell)
            return ci, cj

        sci, scj = _port_cell(net.source_macro, net.source_port, f"src_{net.id}")
        src_cell[net.id] = (sci, scj)
        b_src = _cell_bools(model, sci, scj, cols, rows, f"bsrc_{net.id}")
        b_snks = []
        for si, fs in enumerate(net.sinks):
            tci, tcj = _port_cell(fs.macro, fs.port, f"snk_{net.id}_{si}")
            snk_cell[(net.id, si)] = (tci, tcj)
            b_snks.append(_cell_bools(model, tci, tcj, cols, rows, f"bsnk_{net.id}_{si}"))

        # Flow conservation with placement-dependent source/sinks.
        for i in range(cols):
            for j in range(rows):
                c = (i, j)
                out_arcs = [flow[(net.id, a)] for a in arcs if a[0] == c]
                in_arcs = [flow[(net.id, a)] for a in arcs if a[1] == c]
                model.add(
                    sum(out_arcs) - sum(in_arcs)
                    == k * b_src[c] - sum(b[c] for b in b_snks)
                )

    # -- shared capacity + congestion ---------------------------------------
    used: dict[Edge, cp_model.IntVar] = {}
    saturated: dict[Edge, cp_model.IntVar] = {}
    for e in edges:
        c1, c2 = e
        total = sum(
            arc_used[(net.id, (c1, c2))] + arc_used[(net.id, (c2, c1))]
            for net in problem.nets
        )
        u = model.new_int_var(0, len(problem.nets), f"used_{e}")
        model.add(u == total)
        model.add(u <= cap[e])
        s = model.new_bool_var(f"sat_{e}")
        model.add(u >= cap[e]).only_enforce_if(s)
        model.add(u <= cap[e] - 1).only_enforce_if(s.negated())
        used[e] = u
        saturated[e] = s

    return CoarseVars(
        cell=cell,
        cols=cols,
        rows=rows,
        flow=flow,
        arc_used=arc_used,
        cap=cap,
        used=used,
        saturated=saturated,
        src_cell=src_cell,
        snk_cell=snk_cell,
        v=v,
    )


def extract_coarse(cv: CoarseVars, solver: cp_model.CpSolver) -> CoarseSolution:
    sol = CoarseSolution(cell=cv.cell, cols=cv.cols, rows=cv.rows)
    for (net_id, arc), u in cv.arc_used.items():
        if solver.value(u):
            sol.routes.setdefault(net_id, []).append(arc)
    for e in cv.cap:
        u = solver.value(cv.used[e])
        c = solver.value(cv.cap[e])
        if u or c < cv.cell:
            sol.utilization[e] = (u, c)
    return sol
