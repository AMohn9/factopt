import pytest

from factopt.codec import decode
from factopt.data import vanilla
from factopt.mvp import synthesize

DB = vanilla.DB


def _tiles(entity):
    if entity.name == "assembling-machine-2":
        x0 = int(entity.position.x - 1.5)
        y0 = int(entity.position.y - 1.5)
        return [(x0 + dx, y0 + dy) for dx in range(3) for dy in range(3)]
    return [(int(entity.position.x - 0.5), int(entity.position.y - 0.5))]


def test_synthesize_meets_target_and_is_valid():
    res = synthesize(5.0, DB)
    assert res.validation.meets_target
    assert res.plan.total_machines == 9  # 5 cable + 4 EC
    assert res.blueprint_string.startswith("0")


def test_no_tile_overlaps():
    res = synthesize(5.0, DB)
    occ = {}
    for e in res.blueprint.entities:
        for t in _tiles(e):
            assert t not in occ, f"overlap at {t}: {e.name} vs {occ[t]}"
            occ[t] = e.name


def test_inserter_and_machine_counts():
    res = synthesize(5.0, DB)
    c = res.counts()
    assert c["assembling-machine-2"] == 9
    # 5 cable machines x (1 plate-in + 2 cable-out) = 15
    # 4 EC machines x (2 cable-in + 1 EC-out) = 12 fast inserters
    assert c["fast-inserter"] == 15 + 12
    # 4 EC machines x 2 long-handed iron inserters = 8
    assert c["long-handed-inserter"] == 8


@pytest.mark.parametrize(
    "rate,tier",
    [
        (5.0, "transport-belt"),
        (10.0, "fast-transport-belt"),
        (15.0, "express-transport-belt"),
    ],
)
def test_belt_tier_autoselect(rate, tier):
    res = synthesize(rate, DB)
    assert res.requirements.belt == tier


def test_high_rate_tiles_into_subblocks():
    # 30/s EC exceeds a single lane, so it tiles into independent sub-blocks.
    res = synthesize(30.0, DB)
    assert res.blocks >= 2
    assert res.validation.meets_target
    # No tile overlaps across the tiled sub-blocks.
    occ = {}
    for e in res.blueprint.entities:
        for t in _tiles(e):
            assert t not in occ, f"overlap at {t}"
            occ[t] = e.name


def test_invalid_rate_rejected():
    with pytest.raises(ValueError):
        synthesize(0.0, DB)


# --- generalized chains (red science) ----------------------------------------


def test_red_science_synthesizes_and_meets_target():
    res = synthesize(1.0, DB, target="automation-science-pack")
    assert res.validation.meets_target
    recipes = {e.recipe for e in res.blueprint.entities if e.recipe}
    assert recipes == {"iron-gear-wheel", "automation-science-pack"}
    # 7 science + 1 gear at 1/s.
    c = res.counts()
    assert c["assembling-machine-2"] == 8


def test_red_science_no_overlaps():
    res = synthesize(1.0, DB, target="automation-science-pack")
    occ = {}
    for e in res.blueprint.entities:
        for t in _tiles(e):
            assert t not in occ, f"overlap at {t}"
            occ[t] = e.name


def test_unsupported_chain_rejected():
    # inserter = iron-plate + iron-gear-wheel + electronic-circuit: two non-raw
    # intermediates, not the supported 2-level shape.
    with pytest.raises(ValueError):
        synthesize(1.0, DB, target="inserter")


def test_blueprint_roundtrips():
    res = synthesize(5.0, DB)
    back = decode(res.blueprint_string)
    assert len(back.entities) == len(res.blueprint.entities)
    long_handed = [e for e in back.entities if e.name == "long-handed-inserter"]
    assert len(long_handed) == 8
