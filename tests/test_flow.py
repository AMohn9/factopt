import pytest

from factopt.codec import decode, encode
from factopt.data import vanilla
from factopt.placement import place_flow
from factopt.ratios import solve_ratios

DB = vanilla.DB


def _no_overlaps(p) -> bool:
    occ = set()
    for e in p.machines:
        x0, y0 = int(e.position.x - 1.5), int(e.position.y - 1.5)
        for dx in range(3):
            for dy in range(3):
                t = (x0 + dx, y0 + dy)
                if t in occ:
                    return False
                occ.add(t)
    for ins in p.inserters:
        t = (ins.x, ins.y)
        if t in occ:
            return False
        occ.add(t)
    return True


def test_flow_green_circuit_matches_direct_density():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_flow(plan, DB, cols=10, time_limit_s=30)
    assert p.status in {"OPTIMAL", "FEASIBLE"}
    recipes = [e.recipe for e in p.machines]
    assert recipes.count("copper-cable") == 30
    assert recipes.count("electronic-circuit") == 20
    # Same minimal band count as the hand-specialized direct placer.
    assert p.bands == 5


def test_flow_no_overlaps():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_flow(plan, DB, cols=10, time_limit_s=30)
    assert _no_overlaps(p)


def test_flow_transfer_capacity_feeds_interior_demand():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_flow(plan, DB, cols=10, time_limit_s=30)
    rate = DB.inserters["fast-inserter"].rate
    cable_flow = plan.flows["copper-cable"].consumed_per_sec
    # Every emitted inserter moves copper-cable; total capacity covers demand.
    assert all(ins.item == "copper-cable" for ins in p.inserters)
    assert len(p.inserters) * rate >= cable_flow - 1e-9


def test_flow_handles_rounding_slack_rate():
    # 5/s rounds machine counts up (4 EC have 18/s intake capacity but only 15/s
    # of cable is produced): flow must couple to actual throughput, not nameplate
    # capacity, or this falsely reports infeasible.
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_flow(plan, DB, cols=5, time_limit_s=20)
    assert p.status in {"OPTIMAL", "FEASIBLE"}
    assert [e.recipe for e in p.machines].count("electronic-circuit") == 4
    assert _no_overlaps(p)


def test_flow_single_recipe_has_no_interior_flow():
    # copper-cable alone: nothing is both produced and consumed internally.
    plan = solve_ratios("copper-cable", 10.0, DB)
    p = place_flow(plan, DB, cols=4, time_limit_s=15)
    assert len(p.machines) == 4
    assert p.inserters == []


def test_flow_blueprint_roundtrip():
    plan = solve_ratios("electronic-circuit", 15.0, DB)
    p = place_flow(plan, DB, cols=8, time_limit_s=20)
    back = decode(encode(p.to_blueprint(label="gc-flow-15")))
    assert len(back.entities) == len(p.machines) + len(p.inserters)
    machines = [e for e in back.entities if e.recipe]
    assert all(e.recipe in {"copper-cable", "electronic-circuit"} for e in machines)


def test_flow_rejects_bad_cols():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    with pytest.raises(ValueError):
        place_flow(plan, DB, cols=0)
