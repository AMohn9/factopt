import math

import pytest

from factopt.data import vanilla
from factopt.ratios import solve_ratios


def test_green_circuit_classic_ratio():
    # At equal machine speed the classic ratio is 3 cable : 2 circuit assemblers.
    plan = solve_ratios(
        "electronic-circuit", rate=30.0, db=vanilla.DB, assembler="assembling-machine-2"
    )
    by_recipe = {ln.recipe: ln for ln in plan.lines}

    # 30 EC/s -> 30 EC crafts/s; 90 cable/s -> 45 cable crafts/s.
    assert by_recipe["electronic-circuit"].crafts_per_sec == pytest.approx(30.0)
    assert by_recipe["copper-cable"].crafts_per_sec == pytest.approx(45.0)

    # Exact machines at speed 0.75: EC 20.0, cable 30.0 -> ratio 2:3.
    assert by_recipe["electronic-circuit"].machines_exact == pytest.approx(20.0)
    assert by_recipe["copper-cable"].machines_exact == pytest.approx(30.0)
    assert by_recipe["electronic-circuit"].machines == 20
    assert by_recipe["copper-cable"].machines == 30


def test_raw_inputs():
    plan = solve_ratios("electronic-circuit", rate=30.0, db=vanilla.DB)
    raws = plan.raw_inputs()
    # EC consumes 1 iron-plate/craft -> 30/s; cable consumes 1 copper-plate/craft
    # at 45 crafts/s -> 45/s.
    assert raws["iron-plate"] == pytest.approx(30.0)
    assert raws["copper-plate"] == pytest.approx(45.0)


def test_belt_count_for_output():
    plan = solve_ratios("electronic-circuit", rate=30.0, db=vanilla.DB)
    ec = plan.flows["electronic-circuit"]
    # 30/s over a yellow belt (15/s) is exactly 2 belts.
    assert ec.belts(vanilla.DB.belts["transport-belt"].throughput) == pytest.approx(2.0)


def test_machine_rounding_up():
    # An awkward rate should force a ceil on machine counts.
    plan = solve_ratios(
        "electronic-circuit", rate=10.0, db=vanilla.DB, assembler="assembling-machine-2"
    )
    by_recipe = {ln.recipe: ln for ln in plan.lines}
    ec = by_recipe["electronic-circuit"]
    assert ec.machines_exact == pytest.approx(10.0 * 0.5 / 0.75)
    assert ec.machines == math.ceil(ec.machines_exact)


def test_raw_target_rejected():
    with pytest.raises(ValueError):
        solve_ratios("iron-plate", rate=10.0, db=vanilla.DB)
