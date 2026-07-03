"""Benders-style cuts fed back into the master problem.

Every cut is serializable and carries a human-readable explanation, so a run
log tells the story of why placements changed. Families implemented:

* ``nogood`` — forbid an exact joint placement (position + orientation) of a
  set of macros. Sound for the full macro set; used over a *subset* (failure
  endpoints + blockers) it generalizes across the positions of uninvolved
  macros at the cost of possibly cutting a feasible corner case.
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
    positions: dict[str, tuple[int, int] | tuple[int, int, int]],
    explanation: str,
    kind: str = "nogood",
) -> BendersCut:
    """``positions`` maps macro id to (x, y) or (x, y, orientation)."""
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
            for mid, pos in cut.payload["positions"].items():
                if mid not in v.x:
                    continue
                px, py = pos[0], pos[1]
                lits.append(model.is_ne(v.x[mid], px, f"cut{idx}_{mid}_x"))
                lits.append(model.is_ne(v.y[mid], py, f"cut{idx}_{mid}_y"))
                if len(pos) > 2:
                    lits.append(model.is_ne(v.o_idx[mid], pos[2], f"cut{idx}_{mid}_o"))
            if lits:
                model.add_bool_or(lits)
        elif cut.kind == "pin_access":
            (ma, pa), (mb, pb) = (tuple(t) for t in cut.payload["ports"])
            ax, ay = v.port_access_exprs(ma, pa)
            bx, by = v.port_access_exprs(mb, pb)
            dx = model.new_int_var(-v.max_w, v.max_w, f"cut{idx}_dx")
            dy = model.new_int_var(-v.max_h, v.max_h, f"cut{idx}_dy")
            model.add(dx == ax - bx)
            model.add(dy == ay - by)
            lits = [
                model.is_ne(dx, 0, f"cut{idx}_ndx"),
                model.is_ne(dy, 0, f"cut{idx}_ndy"),
            ]
            model.add_bool_or(lits)
        else:
            raise ValueError(f"unknown cut kind {cut.kind!r}")
