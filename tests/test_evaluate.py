import pytest

from factopt.data import vanilla
from factopt.evaluate import bottleneck, requirements
from factopt.ratios import solve_ratios

DB = vanilla.DB


def _plan():
    return solve_ratios("electronic-circuit", rate=30.0, db=DB, assembler="assembling-machine-2")


def test_belt_requirements():
    req = requirements(_plan(), DB, belt="transport-belt", inserter="fast-inserter")
    belts = {b.item: b.belts for b in req.belt_reqs}
    assert belts["copper-plate"] == 3  # 45/s over 15/s
    assert belts["copper-cable"] == 6  # 90/s over 15/s
    assert belts["iron-plate"] == 2  # 30/s over 15/s
    assert belts["electronic-circuit"] == 2  # 30/s over 15/s
    assert req.total_belts == 13


def test_inserter_requirements():
    req = requirements(_plan(), DB, belt="transport-belt", inserter="fast-inserter")
    ins = {(r.recipe, r.item, r.direction): r for r in req.inserter_reqs}
    # EC machine consumes 4.5 copper-cable/s -> ceil(4.5/2.31)=2 per machine, x20.
    cc_in = ins[("electronic-circuit", "copper-cable", "in")]
    assert cc_in.per_machine == 2
    assert cc_in.total == 40
    # Cable machine outputs 3.0/s -> ceil(3.0/2.31)=2 per machine, x30.
    cc_out = ins[("copper-cable", "copper-cable", "out")]
    assert cc_out.per_machine == 2
    assert cc_out.total == 60


def test_power_and_area():
    req = requirements(_plan(), DB)
    assert req.machine_power_kw == pytest.approx(50 * 150.0)  # 50 AM2 @ 150 kW
    assert req.machine_area_tiles == 50 * 9


def test_full_provision_meets_target():
    bn = bottleneck(_plan(), DB, belt="transport-belt", inserter="fast-inserter")
    assert bn.meets_target
    assert bn.fraction == pytest.approx(1.0)
    assert bn.achievable_rate == pytest.approx(30.0)


def test_belt_starvation_is_detected():
    # Only one yellow belt (15/s) for copper-cable vs the 90/s it needs.
    bn = bottleneck(
        _plan(),
        DB,
        belt="transport-belt",
        inserter="fast-inserter",
        belts_provided={"copper-cable": 1},
    )
    assert not bn.meets_target
    # 15/s split 3-per-craft into EC caps EC crafts at 5/s of 30 nominal -> 1/6.
    assert bn.fraction == pytest.approx(1.0 / 6.0, rel=1e-3)
    assert "copper-cable" in bn.limiter
    assert bn.achievable_rate == pytest.approx(5.0, rel=1e-3)


def test_inserter_starvation_is_detected():
    bn = bottleneck(
        _plan(),
        DB,
        belt="transport-belt",
        inserter="fast-inserter",
        inserters_provided={("electronic-circuit", "copper-cable", "in"): 1},
    )
    assert not bn.meets_target
    # 1 fast inserter (2.31/s) x20 machines / 3 per craft = 15.4 crafts/s of 30.
    assert bn.fraction == pytest.approx(15.4 / 30.0, rel=1e-3)
    assert bn.limiter == "inserter:in:copper-cable"
