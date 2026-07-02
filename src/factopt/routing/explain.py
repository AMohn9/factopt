"""Turn routing failures into Benders cuts for the master (M5).

The goal is attribution: a failure should constrain the macros that caused
it, not just memorize the whole placement. Blockers are found by flooding
the free tiles reachable from the failed net's start (underground jumps
included) and collecting the macros that own the frontier.
"""

from __future__ import annotations

from collections import deque

from factopt.data.database import Database
from factopt.macros.library import MacroProblem
from factopt.master.cuts import BendersCut, nogood_cut, pin_access_cut
from factopt.master.model import MasterSolution
from factopt.routing.multinet import RoutingFailure, RoutingResult

_STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _blocking_macros(
    failure: RoutingFailure,
    solution: MasterSolution,
    db: Database,
    belt: str,
) -> set[str]:
    """Macros owning obstacle tiles on the frontier of the region reachable
    from the failure's start tile."""
    owner: dict[tuple[int, int], str] = {}
    blocked: set[tuple[int, int]] = set()
    for mid, pm in solution.placements.items():
        for t in pm.footprint_tiles():
            owner[t] = mid
            blocked.add(t)

    max_dist = db.belts[belt].underground_max_distance
    w, h = solution.width, solution.height

    def free(t: tuple[int, int]) -> bool:
        return 0 <= t[0] < w and 0 <= t[1] < h and t not in blocked

    start = failure.start
    if start is None or not free(start):
        return set()

    seen = {start}
    frontier_macros: set[str] = set()
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in _STEPS:
            nxt = (x + dx, y + dy)
            if free(nxt):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
            elif nxt in owner:
                frontier_macros.add(owner[nxt])
        # Underground jumps (both endpoints free, straight).
        for dx, dy in _STEPS:
            for sep in range(2, max_dist + 1):
                ex, ey = x + dx * sep, y + dy * sep
                if free((ex, ey)):
                    if (ex, ey) not in seen:
                        seen.add((ex, ey))
                        q.append((ex, ey))
    return frontier_macros


def explain_failures(
    problem: MacroProblem,
    solution: MasterSolution,
    result: RoutingResult,
    db: Database,
    belt: str = "transport-belt",
) -> list[BendersCut]:
    cuts: list[BendersCut] = []
    pos = {mid: (pm.x, pm.y) for mid, pm in solution.placements.items()}

    for f in result.failures:
        if f.kind == "port_conflict" and len(f.ports) == 2:
            cuts.append(
                pin_access_cut(
                    f.ports[0],
                    f.ports[1],
                    next(iter(f.contested_tiles)),
                    explanation=(
                        f"ports {f.ports[0]} and {f.ports[1]} share access tile "
                        f"{next(iter(f.contested_tiles))}; they must not coincide"
                    ),
                )
            )
            continue

        involved: set[str] = {f.source_macro, f.sink_macro}
        if f.kind in ("no_path", "port_blocked"):
            involved |= _blocking_macros(f, solution, db, belt)
            kind = "corridor"
            why = (
                f"net {f.net_id} has no belt path from {f.start} to {f.goal}; "
                f"blocked by {sorted(involved)}"
            )
        else:  # congestion
            for t in f.contested_tiles:
                for mid, pm in solution.placements.items():
                    if (
                        pm.x - 1 <= t[0] <= pm.x2
                        and pm.y - 1 <= t[1] <= pm.y2
                    ):
                        involved.add(mid)
            kind = "corridor"
            why = (
                f"net {f.net_id} could not converge; contested corridor near "
                f"{sorted(f.contested_tiles)[:4]}... involves {sorted(involved)}"
            )
        cuts.append(
            nogood_cut(
                {mid: pos[mid] for mid in sorted(involved)},
                explanation=why,
                kind=kind,
            )
        )

    if result.failures and not cuts:
        cuts.append(
            nogood_cut(pos, explanation="fallback: forbid this exact full placement")
        )
    return cuts
