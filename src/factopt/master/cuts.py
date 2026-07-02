"""Benders-style cuts fed back into the master problem.

Every cut is serializable and carries a human-readable explanation, so a run
log tells the story of why placements changed. Families implemented:

* ``nogood`` — forbid an exact joint placement of a set of macros. Sound for
  the full macro set; used over a *subset* (failure endpoints + blockers) it
  generalizes across the positions of uninvolved macros at the cost of
  possibly cutting a feasible corner case.
* ``pin_access`` — two ports' access tiles must not coincide (detected when
  two nets reserve the same mouth tile).
* ``corridor`` — a no_path/congestion failure attributed to the macros
  walling the region; encoded like a subset nogood but tagged separately so
  reports distinguish geometric dead-ends from plain repetition guards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from factopt.macros.library import MacroProblem
from factopt.master.model import MasterVars


@dataclass(frozen=True)
class BendersCut:
    kind: str  # "nogood" | "pin_access" | "corridor"
    affected_macros: tuple[str, ...]
    explanation: str
    payload: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)


def nogood_cut(
    positions: dict[str, tuple[int, int]], explanation: str, kind: str = "nogood"
) -> BendersCut:
    return BendersCut(
        kind=kind,
        affected_macros=tuple(sorted(positions)),
        explanation=explanation,
        payload={"positions": dict(positions)},
    )


def pin_access_cut(
    a: tuple[str, str], b: tuple[str, str], tile: tuple[int, int], explanation: str
) -> BendersCut:
    return BendersCut(
        kind="pin_access",
        affected_macros=(a[0], b[0]),
        explanation=explanation,
        payload={"ports": [list(a), list(b)], "tile": list(tile)},
    )


def _neq_literal(model, expr, value: int, tag: str):
    """Bool literal that is true iff ``expr != value``."""
    b = model.new_bool_var(tag)
    model.add(expr != value).only_enforce_if(b)
    model.add(expr == value).only_enforce_if(b.negated())
    return b


def _access_expr(problem: MacroProblem, v: MasterVars, macro_id: str, port_id: str):
    from factopt.macros.cell import _SIDE_VEC

    p = problem.macros[macro_id].port(port_id)
    dx, dy = _SIDE_VEC[p.side]
    return (
        v.x[macro_id] + p.local_position[0] + dx,
        v.y[macro_id] + p.local_position[1] + dy,
    )


def apply_cuts(
    cuts: list[BendersCut],
    problem: MacroProblem,
    v: MasterVars,
    coarse_vars=None,
) -> None:
    model = v.model
    for idx, cut in enumerate(cuts):
        if cut.kind in ("nogood", "corridor"):
            lits = []
            for mid, (px, py) in cut.payload["positions"].items():
                if mid not in v.x:
                    continue
                lits.append(_neq_literal(model, v.x[mid], px, f"cut{idx}_{mid}_x"))
                lits.append(_neq_literal(model, v.y[mid], py, f"cut{idx}_{mid}_y"))
            if lits:
                model.add_bool_or(lits)
        elif cut.kind == "pin_access":
            (ma, pa), (mb, pb) = (tuple(t) for t in cut.payload["ports"])
            ax, ay = _access_expr(problem, v, ma, pa)
            bx, by = _access_expr(problem, v, mb, pb)
            dx = model.new_int_var(-v.max_w, v.max_w, f"cut{idx}_dx")
            dy = model.new_int_var(-v.max_h, v.max_h, f"cut{idx}_dy")
            model.add(dx == ax - bx)
            model.add(dy == ay - by)
            lits = [
                _neq_literal(model, dx, 0, f"cut{idx}_ndx"),
                _neq_literal(model, dy, 0, f"cut{idx}_ndy"),
            ]
            model.add_bool_or(lits)
        else:
            raise ValueError(f"unknown cut kind {cut.kind!r}")
