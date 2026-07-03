import pytest

from factopt.model.blueprint import EAST, Blueprint, Entity, Position
from factopt.sim import (
    FactorioNotFound,
    SimJob,
    SimResult,
    Source,
    belt_endpoints,
    run_headless,
)


def test_job_to_lua_is_wellformed():
    job = SimJob(
        blueprint_string="0abcDEF+/=",
        output_item="electronic-circuit",
        sources=[Source(0, 3, "copper-plate"), Source(0, 13, "iron-plate")],
        ticks=3600,
        speed=64.0,
    )
    lua = job.to_lua()
    assert lua.startswith("return {")
    assert "[[0abcDEF+/=]]" in lua  # long-bracket literal wraps the bp string
    assert 'output = "electronic-circuit"' in lua
    assert "ticks = 3600" in lua
    assert 'item = "copper-plate"' in lua and 'item = "iron-plate"' in lua


def test_result_parsing_roundtrip():
    text = (
        '{"done": true, "output_item": "electronic-circuit", '
        '"output_per_sec": 4.5, "ticks": 7200}'
    )
    res = SimResult.from_json(text)
    assert res.output_item == "electronic-circuit"
    assert res.output_per_sec == pytest.approx(4.5)
    assert res.ticks == 7200


def test_result_requires_done_marker():
    with pytest.raises(ValueError):
        SimResult.from_json('{"output_item": "x", "output_per_sec": 1.0}')


def test_run_headless_raises_without_factorio(tmp_path):
    job = SimJob(blueprint_string="0x", output_item="electronic-circuit")
    with pytest.raises(FactorioNotFound):
        run_headless(
            job,
            factorio_path=tmp_path / "does-not-exist",
            scenarios_dir=tmp_path / "scenarios",
            script_output_dir=tmp_path / "script-output",
        )


def test_belt_endpoints_finds_open_ended_belts():
    # A short eastbound belt run: the first tile has nothing feeding it (input
    # endpoint) and the last tile has nothing ahead (output endpoint).
    width, height = 3, 1
    bp = Blueprint(
        entities=[
            Entity("transport-belt", Position(x + 0.5, 0.5), direction=EAST)
            for x in range(width)
        ]
    )
    eps = belt_endpoints(bp)
    kinds = {e.kind for e in eps}
    assert "input" in kinds and "output" in kinds
    # Every endpoint sits on a belt tile within the block bounds.
    for e in eps:
        assert 0 <= e.x < width
        assert 0 <= e.y < height
