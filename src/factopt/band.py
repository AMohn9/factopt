"""Generalized single-recipe band: the production-block primitive for the bus.

A band is one recipe's machine row with up to four belt lanes it interacts with:
two above (a near lane reached by a normal inserter, a far lane reached by a
long-handed inserter) and two below (likewise). This covers any recipe touching
up to four distinct items (e.g. the inserter recipe: iron + gear + EC -> inserter),
which the simple two-lane stacked layout could not.

Each lane is tagged with the item it carries and whether it is an input
(belt -> machine) or output (machine -> belt). The main bus connects these lanes
to the rest of the factory; this module only builds one self-contained band, and
:func:`synthesize_recipe_band` wraps it as an importable test blueprint (inputs
arrive on belts, output leaves on a belt) so a 4-item band can be verified
in-game in isolation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from factopt.codec import encode
from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Blueprint, Entity, Position

# Lane slots around a band, by (row offset, reach). Rows are relative to the
# band's top (the far-top lane = row 0).
#   row 0: top-far lane     (long-handed from the inserter row)
#   row 1: top-near lane    (normal)
#   row 2: top inserter row
#   row 3..5: machine row (3 tall)
#   row 6: bottom inserter row
#   row 7: bottom-near lane (normal)
#   row 8: bottom-far lane  (long-handed)
_ROW_TOP_FAR = 0
_ROW_TOP_NEAR = 1
_ROW_TOP_INS = 2
_ROW_MACHINE = 3
_ROW_BOT_INS = 6
_ROW_BOT_NEAR = 7
_ROW_BOT_FAR = 8
_BAND_HEIGHT = 9

SLOTS = ("top_far", "top_near", "bot_near", "bot_far")
_LANE_ROW = {
    "top_far": _ROW_TOP_FAR,
    "top_near": _ROW_TOP_NEAR,
    "bot_near": _ROW_BOT_NEAR,
    "bot_far": _ROW_BOT_FAR,
}


@dataclass(frozen=True)
class LaneAssign:
    item: str
    flow_dir: str  # "in" (belt -> machine) or "out" (machine -> belt)


_SLOT_SIDE = {"top_near": "top", "top_far": "top", "bot_near": "bot", "bot_far": "bot"}
_SLOT_FAR = {"top_near": False, "top_far": True, "bot_near": False, "bot_far": True}


def _assign_lanes(
    recipe, db: Database, inserter: str, long_inserter: str, assembler: str
) -> dict[str, LaneAssign]:
    """Map recipe items to the four lane slots, balancing inserter load across
    the two machine sides (each side has 3 slots).

    High-flow items prefer near (normal-inserter) slots; the output takes the
    bottom-near slot. Each input is greedily placed in the slot that keeps the
    busier side's inserter count lowest. Raises if a side would exceed 3.
    """
    inputs = list(recipe.ingredients)
    outputs = list(recipe.products)
    if len(inputs) + len(outputs) > 4:
        raise ValueError(
            f"recipe {recipe.name!r} touches {len(inputs) + len(outputs)} items; "
            "a band supports at most 4"
        )

    ins_rate = db.inserters[inserter].rate
    long_rate = db.inserters[long_inserter].rate
    pmc = db.assemblers[assembler].crafting_speed / recipe.time

    def n_for(item: str, far: bool) -> int:
        amt = recipe.ingredients.get(item, 0.0) or recipe.products.get(item, 0.0)
        return max(1, math.ceil(amt * pmc / (long_rate if far else ins_rate) - 1e-9))

    assign: dict[str, LaneAssign] = {}
    side_count = {"top": 0, "bot": 0}
    # Fixed slot preference order (deterministic; never iterate a set).
    free = ["bot_near", "top_near", "top_far", "bot_far"]

    # Output goes on bot_near (a fast slot) by convention.
    if outputs:
        out = outputs[0]
        assign["bot_near"] = LaneAssign(out, "out")
        side_count["bot"] += n_for(out, far=False)
        free.remove("bot_near")

    # Inputs, highest flow first, each into the slot minimizing the busier side
    # (ties broken by the fixed slot order).
    def flow(it: str) -> float:
        return recipe.ingredients[it] * pmc

    for inp in sorted(inputs, key=flow, reverse=True):
        best_slot, best_cost = None, None
        for slot in free:
            side = _SLOT_SIDE[slot]
            n = n_for(inp, _SLOT_FAR[slot])
            cost = max(side_count[side] + n, side_count["top" if side == "bot" else "bot"])
            if best_cost is None or cost < best_cost:
                best_slot, best_cost = slot, cost
        assign[best_slot] = LaneAssign(inp, "in")
        side_count[_SLOT_SIDE[best_slot]] += n_for(inp, _SLOT_FAR[best_slot])
        free.remove(best_slot)

    if side_count["top"] > 3 or side_count["bot"] > 3:
        raise ValueError(
            f"recipe {recipe.name!r} over-subscribes a machine side "
            f"(top={side_count['top']}, bot={side_count['bot']}) at this rate"
        )
    return assign


def _layout_rows(lanes: dict[str, LaneAssign]) -> tuple[dict[str, int], int, int, int, int]:
    """Compute dynamic row offsets, dropping unused far-lane rows so 2-item
    recipes are shorter than 4-item ones. Returns
    (lane_row, machine_row, top_ins_row, bot_ins_row, height)."""
    lane_row: dict[str, int] = {}
    y = 0
    if "top_far" in lanes:
        lane_row["top_far"] = y
        y += 1
    if "top_near" in lanes:
        lane_row["top_near"] = y
        y += 1
    top_ins_row = y
    y += 1
    machine_row = y
    y += 3
    bot_ins_row = y
    y += 1
    if "bot_near" in lanes:
        lane_row["bot_near"] = y
        y += 1
    if "bot_far" in lanes:
        lane_row["bot_far"] = y
        y += 1
    return lane_row, machine_row, top_ins_row, bot_ins_row, y


@dataclass
class Band:
    recipe: str
    n_machines: int
    width: int
    height: int
    lanes: dict[str, LaneAssign]  # slot -> assignment
    lane_row: dict[str, int]  # slot -> row offset within the band
    entities: list[Entity]


def build_band(
    recipe_name: str,
    n_machines: int,
    db: Database,
    assembler: str = "assembling-machine-2",
    inserter: str = "fast-inserter",
    long_inserter: str = "long-handed-inserter",
    with_lane_belts: bool = True,
    belt_items: set[str] | None = None,
    belt_name: str = "transport-belt",
) -> Band:
    """Build one recipe band. If ``with_lane_belts`` the lanes are filled with
    belts (a self-contained, testable block). ``belt_items`` restricts which
    lanes get belts (e.g. raws + the output), leaving the rest for the bus
    router to fill; ``None`` means all lanes."""
    recipe = db.recipes[recipe_name]
    lanes = _assign_lanes(recipe, db, inserter, long_inserter, assembler)
    lane_row, machine_row, top_ins_row, bot_ins_row, height = _layout_rows(lanes)
    width = max(3 * n_machines, 1)
    entities: list[Entity] = []

    def belt(x: int, y: int, direction: int = EAST) -> None:
        entities.append(
            Entity(name=belt_name, position=Position(x + 0.5, y + 0.5), direction=direction)
        )

    def lane_dir(a: LaneAssign) -> int:
        # All lanes flow EAST. Inputs are fed at their WEST end by the bus (where
        # topo-ordered producers sit); outputs are tapped at their EAST end.
        return EAST

    def machine(x: int) -> None:
        entities.append(
            Entity(
                name=assembler, position=Position(x + 1.5, machine_row + 1.5), recipe=recipe_name
            )
        )

    def ins(x: int, y: int, pickup: int, name: str) -> None:
        entities.append(Entity(name=name, position=Position(x + 0.5, y + 0.5), direction=pickup))

    if with_lane_belts:
        for x in range(width):
            for slot, a in lanes.items():
                if belt_items is None or a.item in belt_items:
                    belt(x, lane_row[slot], lane_dir(a))

    ins_rate = db.inserters[inserter].rate
    long_rate = db.inserters[long_inserter].rate
    speed = db.assemblers[assembler].crafting_speed
    pmc = speed / recipe.time

    def n_ins(item: str, rate_: float) -> int:
        amt = recipe.ingredients.get(item, 0.0) or recipe.products.get(item, 0.0)
        return max(1, math.ceil(amt * pmc / rate_ - 1e-9))

    for i in range(n_machines):
        mx = 3 * i
        machine(mx)
        # Up to 3 inserter slots per inserter row; pack near then far.
        top_used = 0
        bot_used = 0
        for slot, a in lanes.items():
            is_far = slot in ("top_far", "bot_far")
            on_top = slot in ("top_far", "top_near")
            name = long_inserter if is_far else inserter
            rate_ = long_rate if is_far else ins_rate
            row = top_ins_row if on_top else bot_ins_row
            count = n_ins(a.item, rate_)
            # An "out" inserter picks the machine (points at the machine); an "in"
            # inserter points at the belt lane it picks from.
            if on_top:
                pickup = NORTH if a.flow_dir == "in" else SOUTH
                base = top_used
                top_used += count
            else:
                pickup = SOUTH if a.flow_dir == "in" else NORTH
                base = bot_used
                bot_used += count
            for k in range(count):
                ins(mx + base + k, row, pickup, name)
        if top_used > 3 or bot_used > 3:
            raise ValueError(
                f"recipe {recipe_name!r} over-subscribes a machine side "
                f"(top={top_used}, bot={bot_used}) at this rate"
            )

    return Band(
        recipe=recipe_name,
        n_machines=n_machines,
        width=width,
        height=height,
        lanes=lanes,
        lane_row=lane_row,
        entities=entities,
    )


def synthesize_recipe_band(
    recipe_name: str,
    n_machines: int,
    db: Database,
    label: str | None = None,
) -> tuple[Blueprint, str]:
    """Wrap a single band as an importable, self-contained test blueprint."""
    band = build_band(recipe_name, n_machines, db, with_lane_belts=True)
    bp = Blueprint(label=label or f"band-{recipe_name}", entities=band.entities)
    return bp, encode(bp)
