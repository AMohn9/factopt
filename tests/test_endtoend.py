"""M6: end-to-end Benders pipeline -- artifacts and optimize() wiring."""

import pytest

from factopt.codec import decode
from factopt.data import vanilla
from factopt.loop import optimize_loop
from factopt.optimize import optimize

DB = vanilla.DB


@pytest.fixture(scope="module")
def gs_loop():
    # Green science at 60/min = 1/s: the plan's first demo target.
    return optimize_loop(
        "logistic-science-pack", 1.0, DB,
        max_iterations=8, master_time_limit_s=15.0, time_budget_s=300.0,
    )


def test_demo_target_produces_importable_blueprint(gs_loop):
    assert gs_loop.feasible, gs_loop.summary()
    bp = decode(gs_loop.best.blueprint_string)
    assert len(bp.entities) > 0
    assert gs_loop.best.validation.ok, str(gs_loop.best.validation)


def test_write_candidate_artifacts(gs_loop, tmp_path):
    from factopt.report import write_candidate

    paths = write_candidate(gs_loop, tmp_path, "green-science-1ps")
    assert paths["report"].exists()
    assert paths["blueprint"].exists()
    assert paths["svg"].exists()
    report = paths["report"].read_text()
    for section in ("# Benders candidate", "## Rate plan", "## Placement", "## Iterations"):
        assert section in report
    assert paths["blueprint"].read_text().startswith("0")
    assert paths["svg"].read_text().startswith("<svg")


def test_optimize_includes_benders_strategy():
    # Small problem (2-level chain) so the loop converges quickly.
    ob = optimize(
        "electronic-circuit", 2.0, DB,
        strategies=("benders",), benders_budget_s=180.0,
    )
    benders = next(c for c in ob.candidates if c.strategy == "benders")
    assert benders.ok, benders.detail
    assert benders.usable, benders.detail
    assert ob.best is not None
    summary = ob.summary()
    assert "benders" in summary
