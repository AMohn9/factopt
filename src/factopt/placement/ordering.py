"""Consumer-adjacency recipe ordering.

Chooses a 1-D order of the plan's recipes minimizing total flow-weighted
producer->consumer distance, so heavy links (e.g. copper-cable ->
electronic-circuit) end up adjacent. A general utility seed for any linear
layout (e.g. deterministic band ordering in tests).

Cost model: for each (producer recipe, consumer recipe, item) link the weight
is the consumer's item draw in items/s; the cost of an order is
``sum(weight * |pos[producer] - pos[consumer]|)``.

Exact by brute force for small plans (<= 8 recipes), CP-SAT linear
arrangement beyond that.
"""

from __future__ import annotations

from itertools import permutations

from factopt.data.database import Database
from factopt.ratios.solver import ProductionPlan

_BRUTE_FORCE_MAX = 8


def _links(plan: ProductionPlan, db: Database) -> list[tuple[str, str, float]]:
    """(producer_recipe, consumer_recipe, items_per_sec) for internal flows."""
    crafts = {ln.recipe: ln.crafts_per_sec for ln in plan.lines}
    producer_of: dict[str, str] = {}
    for r in crafts:
        for prod in db.recipes[r].products:
            producer_of[prod] = r

    out: list[tuple[str, str, float]] = []
    for cons in crafts:
        for item, amount in db.recipes[cons].ingredients.items():
            prod = producer_of.get(item)
            if prod is None or prod == cons:
                continue
            out.append((prod, cons, crafts[cons] * amount))
    return out


def ordering_cost(order: list[str], plan: ProductionPlan, db: Database) -> float:
    """Total flow-weighted producer->consumer distance for ``order``."""
    pos = {r: i for i, r in enumerate(order)}
    return sum(w * abs(pos[p] - pos[c]) for p, c, w in _links(plan, db))


def order_recipes(plan: ProductionPlan, db: Database) -> list[str]:
    """Order of the plan's recipes minimizing :func:`ordering_cost`."""
    recipes = sorted(ln.recipe for ln in plan.lines)
    if len(recipes) <= 1:
        return recipes
    if len(recipes) <= _BRUTE_FORCE_MAX:
        return _brute_force(recipes, plan, db)
    return _cpsat(recipes, plan, db)


def _brute_force(recipes: list[str], plan: ProductionPlan, db: Database) -> list[str]:
    links = _links(plan, db)
    best: tuple[float, tuple[str, ...]] | None = None
    for perm in permutations(recipes):
        pos = {r: i for i, r in enumerate(perm)}
        cost = sum(w * abs(pos[p] - pos[c]) for p, c, w in links)
        # Tie-break on the permutation itself for determinism (an order and
        # its reversal always cost the same).
        key = (cost, perm)
        if best is None or key < best:
            best = key
    return list(best[1])


def _cpsat(
    recipes: list[str],
    plan: ProductionPlan,
    db: Database,
    time_limit_s: float = 10.0,
) -> list[str]:
    from ortools.sat.python import cp_model

    links = _links(plan, db)
    n = len(recipes)
    scale = 1000

    model = cp_model.CpModel()
    pos = {r: model.new_int_var(0, n - 1, f"pos_{r}") for r in recipes}
    model.add_all_different(pos.values())

    terms = []
    for p, c, w in links:
        dist = model.new_int_var(0, n - 1, f"d_{p}_{c}")
        model.add_abs_equality(dist, pos[p] - pos[c])
        terms.append(int(round(w * scale)) * dist)
    model.minimize(sum(terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return recipes  # degenerate; caller still gets a valid permutation
    return sorted(recipes, key=lambda r: solver.value(pos[r]))
