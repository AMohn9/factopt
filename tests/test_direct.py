import pytest

from factopt.codec import decode, encode
from factopt.data import vanilla
from factopt.evaluate import bottleneck, requirements
from factopt.placement import place_direct, place_direct_banded
from factopt.ratios import solve_ratios

DB = vanilla.DB
DIRECT = frozenset({"copper-cable"})


# --- evaluator direct-insertion extension ------------------------------------


def test_direct_drops_cable_belt_and_halves_cable_inserters():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    bus = requirements(plan, DB, belt="fast-transport-belt", inserter="fast-inserter")
    direct = requirements(
        plan, DB, belt="fast-transport-belt", inserter="fast-inserter", direct_items=DIRECT
    )
    # No copper-cable belt lane when direct-inserted.
    assert any(b.item == "copper-cable" for b in bus.belt_reqs)
    assert not any(b.item == "copper-cable" for b in direct.belt_reqs)
    # Far fewer inserters overall (cable in+out collapse to a single transfer).
    assert direct.total_inserters < bus.total_inserters
    transfer = [i for i in direct.inserter_reqs if i.direction == "transfer"]
    assert len(transfer) == 1 and transfer[0].item == "copper-cable"


def test_direct_bottleneck_meets_target():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    bn = bottleneck(
        plan, DB, belt="fast-transport-belt", inserter="fast-inserter", direct_items=DIRECT
    )
    assert bn.meets_target


def test_direct_transfer_starvation_detected():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    bn = bottleneck(
        plan,
        DB,
        belt="fast-transport-belt",
        inserter="fast-inserter",
        direct_items=DIRECT,
        inserters_provided={("(transfer)", "copper-cable", "transfer"): 1},
    )
    assert not bn.meets_target
    assert bn.limiter == "direct:copper-cable"


# --- CP-SAT direct placement -------------------------------------------------


def test_place_direct_structure():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct(plan, DB, cols=10, time_limit_s=30)
    assert p.status in {"OPTIMAL", "FEASIBLE"}
    recipes = [e.recipe for e in p.machines]
    assert recipes.count("copper-cable") == 30
    assert recipes.count("electronic-circuit") == 20
    # 50 machines packed into a minimal number of bands at width 10.
    assert p.bands == 5


def test_place_direct_no_overlaps():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct(plan, DB, cols=10, time_limit_s=30)
    occ = set()
    for e in p.machines:
        x0, y0 = int(e.position.x - 1.5), int(e.position.y - 1.5)
        for dx in range(3):
            for dy in range(3):
                t = (x0 + dx, y0 + dy)
                assert t not in occ
                occ.add(t)
    for ins in p.inserters:
        t = (ins.x, ins.y)
        assert t not in occ
        occ.add(t)


def test_place_direct_transfer_capacity_sufficient():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct(plan, DB, cols=10, time_limit_s=30)
    rate = DB.inserters["fast-inserter"].rate
    cable_flow = plan.flows["copper-cable"].consumed_per_sec
    assert len(p.inserters) * rate >= cable_flow - 1e-9


def test_place_direct_blueprint_roundtrip():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct(plan, DB, cols=10, time_limit_s=30)
    bp = p.to_blueprint(label="gc-direct-30")
    back = decode(encode(bp))
    assert len(back.entities) == len(p.machines) + len(p.inserters)


def test_place_direct_rejects_non_green_circuit():
    plan = solve_ratios("copper-cable", 10.0, DB)
    with pytest.raises(ValueError):
        place_direct(plan, DB, cols=4)


# --- banded E/C/C/E placement (reference structure) --------------------------


def test_banded_reproduces_reference_structure():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct_banded(plan, DB, cols=15, band_pattern=("E", "C", "C", "E"))
    assert p.bands == 4
    recipes = [e.recipe for e in p.machines]
    assert recipes.count("copper-cable") == 30
    assert recipes.count("electronic-circuit") == 20
    # Cable flow balances: total injected == total EC demand (in scaled units).
    assert sum(p.cable_flow.values()) == 20 * 45


def test_banded_central_channel_is_clear():
    # The gap between the two cable bands carries no cable transfer (free for
    # the plate I/O lane): no inserters land in that row.
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct_banded(plan, DB, cols=15)
    # band1 occupies y4..6, band2 y8..10, so the C/C gap (plate channel) is y7.
    assert not any(ins.y == 7 for ins in p.inserters)


def test_banded_no_overlaps():
    plan = solve_ratios("electronic-circuit", 30.0, DB)
    p = place_direct_banded(plan, DB, cols=15)
    occ = set()
    for e in p.machines:
        x0, y0 = int(e.position.x - 1.5), int(e.position.y - 1.5)
        for dx in range(3):
            for dy in range(3):
                t = (x0 + dx, y0 + dy)
                assert t not in occ
                occ.add(t)
    for ins in p.inserters:
        t = (ins.x, ins.y)
        assert t not in occ
        occ.add(t)
