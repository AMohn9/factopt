import pytest

from factopt.codec import decode
from factopt.data import vanilla
from factopt.optimize import optimize

DB = vanilla.DB


def test_optimize_prefers_compact_for_green_circuits():
    ob = optimize("electronic-circuit", 5.0, DB)
    assert ob.best is not None
    assert ob.best.strategy == "compact"
    # The tight generator beats the general bus on footprint.
    bus = next(c for c in ob.candidates if c.strategy == "bus")
    assert ob.best.area < bus.area


def test_optimize_uses_line_for_green_science():
    ob = optimize("logistic-science-pack", 1.0, DB)
    # compact can't do this multi-level chain; the optimizer-ordered `line`
    # completes it and beats the loose `bus` on footprint.
    compact = next(c for c in ob.candidates if c.strategy == "compact")
    assert not compact.ok
    assert ob.best is not None
    assert ob.best.strategy == "line"
    assert ob.best.complete
    bus = next(c for c in ob.candidates if c.strategy == "bus")
    if bus.usable:
        assert ob.best.area <= bus.area


def test_optimize_best_is_usable_and_importable():
    for target, rate in [
        ("electronic-circuit", 30.0),
        ("automation-science-pack", 1.0),
        ("logistic-science-pack", 1.0),
    ]:
        ob = optimize(target, rate, DB)
        assert ob.best is not None and ob.best.usable
        # The winning blueprint string decodes (is importable).
        back = decode(ob.blueprint_string)
        assert len(back.entities) > 0


def test_optimize_rejects_bad_rate():
    with pytest.raises(ValueError):
        optimize("electronic-circuit", 0.0, DB)
