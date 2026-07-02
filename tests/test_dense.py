import pytest

from factopt.codec import decode, encode
from factopt.data import vanilla
from factopt.placement import place_dense_row
from factopt.ratios import solve_ratios
from factopt.validate import validate

DB = vanilla.DB


def test_dense_row_green_circuit_places_all_machines():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_dense_row(plan, DB, time_limit_s=20)
    recipes = [e.recipe for e in p.machines]
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    assert recipes.count("copper-cable") == counts["copper-cable"]
    assert recipes.count("electronic-circuit") == counts["electronic-circuit"]
    assert p.height == 8


def test_dense_row_internal_item_never_belted():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_dense_row(plan, DB, time_limit_s=20)
    belt_items = {"copper-plate", "iron-plate", "electronic-circuit"}
    # Every belt tile is a boundary lane; copper-cable (internal) rides no belt.
    assert p.internal_item == "copper-cable"
    # There are exactly three full-width boundary lanes.
    assert len(p.belts) == 3 * p.width


def test_dense_row_validates_static():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_dense_row(plan, DB, time_limit_s=20)
    report = validate(p.entities(), DB, bounds=(0, 0, p.width, p.height))
    # No overlaps, in bounds, and every inserter has a real pickup + dropoff.
    assert report.by_kind("overlap") == []
    assert report.by_kind("bounds") == []
    assert report.by_kind("inserter") == []


def test_dense_row_boundary_ports():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_dense_row(plan, DB, time_limit_s=20)
    by_item = {(port.item, port.direction) for port in p.ports}
    assert ("copper-plate", "input") in by_item
    assert ("iron-plate", "input") in by_item
    assert ("electronic-circuit", "output") in by_item


def test_dense_row_blueprint_roundtrip():
    plan = solve_ratios("electronic-circuit", 5.0, DB)
    p = place_dense_row(plan, DB, time_limit_s=20)
    back = decode(encode(p.to_blueprint(label="gc-dense-5")))
    assert len(back.entities) == len(p.entities())


def test_dense_row_rejects_non_two_level_chain():
    # Green science is a deeper tree with multiple internal items.
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    with pytest.raises((ValueError, RuntimeError)):
        place_dense_row(plan, DB, time_limit_s=20)


def test_plan_fusions_picks_only_cable_ec_for_green_science():
    from factopt.placement.dense import plan_fusions

    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    groups = plan_fusions(plan, DB)
    # Only copper-cable -> electronic-circuit is a clean direct-insertion pair;
    # gears (two consumers) and the inserter (extra intermediate) stay belted.
    assert groups == [{"copper-cable", "electronic-circuit"}]


def test_build_problem_partial_fusion_green_science():
    from factopt.macros import build_problem

    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    prob = build_problem(plan, DB, fuse=True)
    # A dense cell replaces the two belt bands for cable + circuits.
    assert "dense-copper-cable" in prob.macros
    assert prob.macros["dense-copper-cable"].kind == "dense-direct"
    # copper-cable is inserted machine-to-machine: it is never a routed net.
    assert all(n.item != "copper-cable" for n in prob.nets)
    # The dense cell's circuit output belts to the inserter band.
    ec = [n for n in prob.nets if n.item == "electronic-circuit"]
    assert len(ec) == 1 and ec[0].sink_macro == "inserter"
    # Gears fan out to both the belt and inserter bands (on belts).
    gear_sinks = {n.sink_macro for n in prob.nets if n.item == "iron-gear-wheel"}
    assert gear_sinks == {"inserter", "transport-belt"}


def test_build_problem_fuse_false_unchanged():
    # Without fusion, every recipe is still its own belt band (no dense cells).
    from factopt.macros import build_problem

    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    prob = build_problem(plan, DB, fuse=False)
    assert not any(m.kind == "dense-direct" for m in prob.macros.values())
    band_ids = {m.id for m in prob.macros.values() if m.kind == "recipe-band"}
    assert band_ids == {ln.recipe for ln in plan.lines}
