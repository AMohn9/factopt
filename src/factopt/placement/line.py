"""Optimizer-driven line placement.

A first step in moving general-chain layout off the loose ``bus`` heuristic and
onto the optimizer: it drives the (verified) band + routing emission from the
consumer-adjacency ordering (:func:`factopt.placement.ordering.order_recipes`)
and packs with the tightest inter-band gaps that still route completely.

That directly targets the ``bus`` complaints -- better ordering (producers near
consumers) and much smaller footprints -- while reusing emission we trust. Full
direct-insertion / shared-lane emission (dropping the through-belts entirely) is
the next layer built on top of this ordering.
"""

from __future__ import annotations

from factopt.bus import BusResult, synthesize_bus
from factopt.data.database import Database
from factopt.placement.ordering import order_recipes
from factopt.ratios.solver import solve_ratios

# Gap (hgap, vgap) sizes to try, tightest first; the first fully-routed layout
# wins, otherwise we keep the most-complete attempt.
_GAP_LADDER = [(1, 1), (1, 2), (2, 3), (3, 4), (4, 5)]


def synthesize_line(
    rate: float,
    db: Database,
    target: str,
    belt: str = "transport-belt",
    inserter: str = "fast-inserter",
    label: str | None = None,
) -> BusResult:
    """Lay out a block using the adjacency-optimized recipe order and the
    tightest routable gaps. Returns the tightest complete layout, or the
    most-complete attempt if none route fully."""
    plan = solve_ratios(target, rate, db)
    opt_order = order_recipes(plan, db)

    best: BusResult | None = None
    # Prefer the adjacency-optimized order; fall back to bus's default order,
    # which can route some chains the optimized order happens to block.
    for order in (opt_order, None):
        for hgap, vgap in _GAP_LADDER:
            res = synthesize_bus(
                rate, db, target, belt=belt, inserter=inserter, label=label,
                order=order, hgap=hgap, vgap=vgap,
            )
            if res.complete:
                return res
            if best is None or len(res.unrouted) < len(best.unrouted):
                best = res
    return best
