"""Belt-lane transport-band placement (fan-out chains).

:mod:`factopt.placement.flow` couples interior item flow as *vertical* direct
insertion, which is dense but requires every consumer to sit next to a producer.
That fails when a scarce producer must feed many consumers (e.g. red science:
one gear machine feeding seven science machines) -- there simply aren't enough
adjacencies. The classic fix is a **distribution belt lane**: the producer drops
the interior item onto a horizontal belt, and any number of consumers pick it off
downstream. This is the no-splitter shared-lane trick the MVP generator already
verified in-game, here generalized and packed by machine count.

Layout (one interior belt lane feeding a band above and a band below it)::

    band TOP     : machines (row 0-2)
    inserter row : TOP machines inject onto / extract from the lane (row 3)
    belt lane    : the interior item, flowing EAST (row 4)
    inserter row : BOTTOM machines inject onto / extract from the lane (row 5)
    band BOTTOM  : machines (row 6-8)

Producers are packed at the west columns so the item is injected upstream of the
consumers that pull it eastward. Raw inputs and the final product are block
boundary I/O and left to the routing pass, as with the other placers.

Scope: 2-level chains with a single interior item (product = intermediate + raw;
intermediate = raw), which covers green circuits and red science. Larger jobs
that exceed two bands, or chains with multiple interior items, need lane tiling /
multiple lanes -- the next extension.

Belt/inserter *facing* follows the pickup convention used across factopt and the
in-game-verified MVP; still worth a sanity import when first exercised on a new
chain.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, Blueprint, Entity, Position
from factopt.ratios.solver import ProductionPlan

_BAND_H = 3
# Row offsets within the 9-tall transport band.
_TOP_BAND = 0
_TOP_INS = 3
_LANE = 4
_BOT_INS = 5
_BOT_BAND = 6
_HEIGHT = 9
_INSERTERS_PER_SIDE = 3


@dataclass(frozen=True)
class BeltInserter:
    x: int
    y: int
    direction: int
    item: str


@dataclass
class BeltPlacement:
    plan: ProductionPlan
    interior_item: str
    belt: str
    cols: int
    width: int
    height: int
    machines: list[Entity] = field(default_factory=list)
    inserters: list[BeltInserter] = field(default_factory=list)
    belts: list[Entity] = field(default_factory=list)

    @property
    def area(self) -> int:
        return self.width * self.height

    def to_blueprint(self, label: str | None = None) -> Blueprint:
        ents = list(self.machines) + list(self.belts)
        for ins in self.inserters:
            ents.append(
                Entity(
                    name="fast-inserter",
                    position=Position(ins.x + 0.5, ins.y + 0.5),
                    direction=ins.direction,
                )
            )
        return Blueprint(label=label, entities=ents)


def _roles(plan: ProductionPlan, db: Database) -> tuple[str, str, str]:
    """Return (interior_item, producer_recipe, consumer_recipe) for a single-
    interior 2-level chain. Raises if the plan isn't that shape."""
    produced: dict[str, str] = {}
    consumed: dict[str, list[str]] = {}
    for line in plan.lines:
        recipe = db.recipes[line.recipe]
        for item in recipe.products:
            produced[item] = line.recipe
        for item in recipe.ingredients:
            consumed.setdefault(item, []).append(line.recipe)
    interior = sorted(set(produced) & set(consumed))
    if len(interior) != 1:
        raise ValueError(
            f"belt placement handles a single interior item; got {interior} "
            f"(multi-lane / tiled layouts are not supported yet)"
        )
    item = interior[0]
    consumers = consumed[item]
    if len(consumers) != 1:
        raise ValueError(f"interior item {item!r} has multiple consumers {consumers}")
    return item, produced[item], consumers[0]


def _select_belt(flow: float, db: Database, belt: str | None) -> str:
    tiers = [belt] if belt else sorted(db.belts, key=lambda b: db.belts[b].throughput)
    for name in tiers:
        if name not in db.belts:
            raise ValueError(f"unknown belt {name!r}")
        if db.belts[name].throughput >= flow - 1e-9:
            return name
    raise ValueError(
        f"interior flow {flow:g}/s exceeds a single {tiers[-1]} lane; "
        "multi-lane distribution is not supported yet"
    )


def place_belt(
    plan: ProductionPlan,
    db: Database,
    cols: int,
    inserter: str = "fast-inserter",
    belt: str | None = None,
) -> BeltPlacement:
    """Place a 2-level chain as two machine bands sharing one interior belt lane.

    ``cols`` sets the width (machine columns). Raises if the machines don't fit in
    two bands or the interior flow exceeds a single belt lane.
    """
    if cols < 1:
        raise ValueError("cols must be >= 1")

    item, prod_recipe, cons_recipe = _roles(plan, db)
    counts = {line.recipe: line.machines for line in plan.lines}
    n_prod, n_cons = counts[prod_recipe], counts[cons_recipe]
    if n_prod + n_cons > 2 * cols:
        raise ValueError(
            f"{n_prod + n_cons} machines exceed two {cols}-wide bands; "
            f"use cols >= {math.ceil((n_prod + n_cons) / 2)} or tile the block"
        )

    interior_flow = max(
        plan.flows[item].produced_per_sec, plan.flows[item].consumed_per_sec
    )
    belt_name = _select_belt(interior_flow, db, belt)

    speed = db.assemblers[plan.assembler].crafting_speed
    ins_rate = db.inserters[inserter].rate

    def per_machine(recipe_name: str) -> float:
        return speed / db.recipes[recipe_name].time

    inject_per = db.recipes[prod_recipe].products[item] * per_machine(prod_recipe)
    extract_per = db.recipes[cons_recipe].ingredients[item] * per_machine(cons_recipe)
    n_inject = max(1, math.ceil(inject_per / ins_rate - 1e-9))
    n_extract = max(1, math.ceil(extract_per / ins_rate - 1e-9))
    if max(n_inject, n_extract) > _INSERTERS_PER_SIDE:
        raise ValueError(
            f"a machine needs more than {_INSERTERS_PER_SIDE} lane inserters at "
            f"this rate; tile the block into lower-rate sub-blocks"
        )

    width = cols * _BAND_H
    placement = BeltPlacement(
        plan=plan, interior_item=item, belt=belt_name, cols=cols,
        width=width, height=_HEIGHT,
    )

    # Producers packed at the west (upstream on the EAST-flowing lane), then
    # consumers, filling the TOP band left-to-right then the BOTTOM band.
    slots = [(_TOP_BAND, c) for c in range(cols)] + [(_BOT_BAND, c) for c in range(cols)]
    for idx, (band_y, col) in enumerate(slots):
        if idx >= n_prod + n_cons:
            break
        is_producer = idx < n_prod
        recipe = prod_recipe if is_producer else cons_recipe
        placement.machines.append(
            Entity(
                name=plan.assembler,
                position=Position(col * _BAND_H + 1.5, band_y + 1.5),
                recipe=recipe,
            )
        )
        on_top = band_y == _TOP_BAND
        ins_y = _TOP_INS if on_top else _BOT_INS
        # Pickup-direction convention: inject picks from the machine, extract
        # picks from the lane. TOP machines sit above the lane, BOTTOM below.
        if is_producer:
            direction = NORTH if on_top else SOUTH  # pick from the machine
            n = n_inject
        else:
            direction = SOUTH if on_top else NORTH  # pick from the lane
            n = n_extract
        for k in range(n):
            placement.inserters.append(
                BeltInserter(x=col * _BAND_H + k, y=ins_y, direction=direction, item=item)
            )

    # The shared interior lane spans the full width, flowing east.
    for x in range(width):
        placement.belts.append(
            Entity(name=belt_name, position=Position(x + 0.5, _LANE + 0.5), direction=EAST)
        )

    return placement
