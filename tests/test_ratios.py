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


def test_supplied_input_prunes_subtree():
    # Green science pulls in the circuit sub-tree (via inserters).
    base = {ln.recipe for ln in solve_ratios("logistic-science-pack", 1.0, vanilla.DB).lines}
    assert {"electronic-circuit", "copper-cable"} <= base

    supplied = solve_ratios(
        "logistic-science-pack", 1.0, vanilla.DB, inputs=["electronic-circuit"]
    )
    recipes = {ln.recipe for ln in supplied.lines}
    # Supplying the circuit stops it (and its only-for-circuits copper-cable
    # feeder) from being built inside the block.
    assert "electronic-circuit" not in recipes
    assert "copper-cable" not in recipes
    # It now enters as a raw input instead, and copper-plate is no longer needed.
    raws = supplied.raw_inputs()
    assert raws["electronic-circuit"] > 0
    assert supplied.flows["electronic-circuit"].is_raw
    assert "copper-plate" not in raws


def test_supplied_input_cannot_be_target():
    with pytest.raises(ValueError):
        solve_ratios(
            "electronic-circuit", 10.0, vanilla.DB, inputs=["electronic-circuit"]
        )


def test_with_inputs_leaves_original_db_untouched():
    db = vanilla.DB
    assert not db.is_raw("electronic-circuit")
    aug = db.with_inputs(["electronic-circuit"])
    assert aug.is_raw("electronic-circuit")
    assert not db.is_raw("electronic-circuit")  # original unchanged
    # Only rawness changes; the recipe is still known.
    assert aug.recipe_for("electronic-circuit") is not None
    # No items is a no-op that returns the same instance.
    assert db.with_inputs([]) is db
