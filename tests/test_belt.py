import pytest

from factopt.codec import decode, encode
from factopt.data import vanilla
from factopt.model.blueprint import EAST
from factopt.placement import place_belt
from factopt.ratios import solve_ratios

DB = vanilla.DB


def _no_overlaps(p) -> bool:
    occ = set()
    for e in p.machines:
        x0, y0 = int(e.position.x - 1.5), int(e.position.y - 1.5)
        for dx in range(3):
            for dy in range(3):
                t = (x0 + dx, y0 + dy)
                if t in occ:
                    return False
                occ.add(t)
    for ins in p.inserters:
        if (ins.x, ins.y) in occ:
            return False
        occ.add((ins.x, ins.y))
    for b in p.belts:
        t = (int(b.position.x - 0.5), int(b.position.y - 0.5))
        if t in occ:
            return False
        occ.add(t)
    return True


def test_belt_red_science_fans_out():
    # The case pure vertical direct insertion can't do: 1 producer -> 7 consumers.
    plan = solve_ratios("automation-science-pack", 1.0, DB)
    p = place_belt(plan, DB, cols=4)
    assert p.interior_item == "iron-gear-wheel"
    recipes = [e.recipe for e in p.machines]
    assert recipes.count("iron-gear-wheel") == 1
    assert recipes.count("automation-science-pack") == 7
    # A shared interior lane spans the full width, flowing east.
    assert len(p.belts) == p.width
    assert all(b.direction == EAST for b in p.belts)


def test_belt_no_overlaps():
    plan = solve_ratios("automation-science-pack", 1.0, DB)
    assert _no_overlaps(place_belt(plan, DB, cols=4))
    plan2 = solve_ratios("electronic-circuit", 5.0, DB)
    assert _no_overlaps(place_belt(plan2, DB, cols=5))


def test_belt_interior_flow_fits_selected_lane():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_belt(plan, DB, cols=5)
    flow = plan.flows[p.interior_item].consumed_per_sec
    assert DB.belts[p.belt].throughput >= flow - 1e-9


def test_belt_blueprint_roundtrip():
    plan = solve_ratios("automation-science-pack", 1.0, DB)
    p = place_belt(plan, DB, cols=4)
    back = decode(encode(p.to_blueprint(label="red-sci-belt")))
    assert len(back.entities) == len(p.machines) + len(p.inserters) + len(p.belts)


def test_belt_rejects_too_small_cols():
    plan = solve_ratios("automation-science-pack", 1.0, DB)
    with pytest.raises(ValueError):
        place_belt(plan, DB, cols=3)  # 8 machines can't fit two 3-wide bands
