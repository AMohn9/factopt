import pytest

from factopt.codec import decode
from factopt.data import vanilla
from factopt.optimize import DEFAULT_STRATEGIES, optimize

DB = vanilla.DB


def test_default_strategies_are_loop_only():
    # The optimizer is now purely the general Benders loop (belt + dense fusion).
    assert DEFAULT_STRATEGIES == ("benders", "dense")


def test_optimize_dense_strategy_direct_inserts_green_circuits():
    # The `dense` strategy packs the copper-cable -> electronic-circuit chain as
    # one direct-insertion cell and routes only the raws + product; it should
    # yield a complete, importable, target-meeting block.
    ob = optimize(
        "electronic-circuit", 5.0, DB, strategies=("dense",), benders_budget_s=90.0
    )
    dense = next(c for c in ob.candidates if c.strategy == "dense")
    assert dense.usable, dense.detail
    back = decode(dense.blueprint_string)
    # The internal copper-cable rides no belt: no lane carries it (it is moved
    # machine-to-machine), so every assembler is present and wired.
    recipes = [e.recipe for e in back.entities if e.recipe]
    assert recipes.count("copper-cable") > 0
    assert recipes.count("electronic-circuit") > 0


def test_optimize_best_is_usable_and_importable():
    ob = optimize(
        "electronic-circuit", 5.0, DB, strategies=("dense",), benders_budget_s=90.0
    )
    assert ob.best is not None and ob.best.usable
    # The winning blueprint string decodes (is importable).
    back = decode(ob.blueprint_string)
    assert len(back.entities) > 0


def test_optimize_rejects_bad_rate():
    with pytest.raises(ValueError):
        optimize("electronic-circuit", 0.0, DB)
