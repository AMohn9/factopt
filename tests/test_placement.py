import pytest

from factopt.codec import decode, encode
from factopt.data import vanilla
from factopt.placement import place_block
from factopt.ratios import solve_ratios

DB = vanilla.DB


def _rects(placement):
    """Yield (x, y, w, h) for every placed tile-rectangle."""
    for m in placement.machines:
        yield (m.x, m.y, m.width, m.height)
    for i in placement.inserters:
        yield (i.x, i.y, 1, 1)


def _overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def test_small_block_places_without_overlap():
    plan = solve_ratios("electronic-circuit", rate=1.0, db=DB, assembler="assembling-machine-2")
    placement = place_block(plan, DB, width=8, inserter="fast-inserter", time_limit_s=10.0)

    # 2 machines (1 cable + 1 EC), 7 inserters expected.
    assert len(placement.machines) == 2
    assert len(placement.inserters) == 7

    rects = list(_rects(placement))
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert not _overlap(rects[i], rects[j]), (rects[i], rects[j])


def test_entities_in_bounds():
    plan = solve_ratios("electronic-circuit", rate=1.0, db=DB)
    placement = place_block(plan, DB, width=8, time_limit_s=10.0)
    for x, y, w, h in _rects(placement):
        assert 0 <= x and x + w <= placement.width
        assert 0 <= y and y + h <= placement.height


def test_inserters_adjacent_to_their_machine():
    plan = solve_ratios("electronic-circuit", rate=1.0, db=DB)
    placement = place_block(plan, DB, width=8, time_limit_s=10.0)
    for ins in placement.inserters:
        m = placement.machines[ins.machine_index]
        # Inserter tile must be orthogonally adjacent to the 3x3 footprint.
        in_col = m.x <= ins.x <= m.x + 2
        in_row = m.y <= ins.y <= m.y + 2
        touches = (
            (ins.x == m.x - 1 and in_row)
            or (ins.x == m.x + 3 and in_row)
            or (ins.y == m.y - 1 and in_col)
            or (ins.y == m.y + 3 and in_col)
        )
        assert touches, (ins, m)


def test_blueprint_roundtrip():
    plan = solve_ratios("electronic-circuit", rate=1.0, db=DB)
    placement = place_block(plan, DB, width=8, time_limit_s=10.0)
    bp = placement.to_blueprint(label="green-circuits-1ps")
    s = encode(bp)
    back = decode(s)
    assert len(back.entities) == len(placement.machines) + len(placement.inserters)
    # Machines carry their recipe through the roundtrip.
    machines = [e for e in back.entities if e.name == "assembling-machine-2"]
    assert all(e.recipe in {"electronic-circuit", "copper-cable"} for e in machines)


def test_width_too_small_rejected():
    plan = solve_ratios("electronic-circuit", rate=1.0, db=DB)
    with pytest.raises(ValueError):
        place_block(plan, DB, width=2)
