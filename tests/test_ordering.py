from factopt.data import vanilla
from factopt.placement.ordering import order_recipes, ordering_cost
from factopt.ratios import solve_ratios

DB = vanilla.DB


def _depth_order(plan):
    """Reproduce bus.py's topological-depth ordering (the baseline to beat)."""
    from functools import lru_cache

    counts = {ln.recipe: ln.machines for ln in plan.lines}
    producer_of = {}
    for r in counts:
        for prod in DB.recipes[r].products:
            producer_of[prod] = r

    @lru_cache(maxsize=None)
    def depth(item):
        if item not in producer_of:
            return 0
        return 1 + max((depth(i) for i in DB.recipes[producer_of[item]].ingredients), default=0)

    return sorted(counts, key=lambda r: max(depth(p) for p in DB.recipes[r].products))


def test_ordering_beats_depth_order_for_green_science():
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    opt = order_recipes(plan, DB)
    baseline = _depth_order(plan)
    assert ordering_cost(opt, plan, DB) <= ordering_cost(baseline, plan, DB)


def test_ordering_makes_key_links_adjacent():
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    order = order_recipes(plan, DB)
    pos = {r: i for i, r in enumerate(order)}
    # The wire->circuit and circuit->inserter links should be direct-insertable.
    assert abs(pos["copper-cable"] - pos["electronic-circuit"]) == 1
    assert abs(pos["electronic-circuit"] - pos["inserter"]) == 1


def test_ordering_is_permutation():
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    order = order_recipes(plan, DB)
    assert sorted(order) == sorted(ln.recipe for ln in plan.lines)


def test_ordering_trivial_chains():
    # 2-level chain: two recipes, produced-adjacent by construction.
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    order = order_recipes(plan, DB)
    assert set(order) == {"copper-cable", "electronic-circuit"}
