"""Build a :class:`~factopt.data.database.Database` from Draftsman's game data.

Draftsman ships prototype data extracted from Wube's ``factorio-data`` repo,
defaulting to Factorio 2.0. This module adapts that raw prototype data into
factopt's small typed structures.

Recipe prototypes come in a few shapes we normalize away (handling both the 2.0
and 1.1 forms, so a re-pinned data set still loads):

* ``ingredients`` / ``results`` as ``{"name": ..., "amount": ...}`` dicts (2.0)
  or ``["name", count]`` pairs (1.1); the dict form also carries fluids, which we
  detect and skip -- the belt pipeline can't route fluids yet;
* a flat ``result`` (+ ``result_count``) instead of a ``results`` list;
* a ``normal`` / ``expensive`` difficulty split (1.1; we always take ``normal``).

Inserter *throughput* is a gameplay-derived quantity (rotation + extension speed
+ hand stack size + bonuses), not a clean prototype field, so those rates stay
curated in :mod:`factopt.data.vanilla`; everything else comes from the data.
"""

from __future__ import annotations

import re

from draftsman.data import entities as _entities
from draftsman.data import recipes as _recipes

from factopt.model.game import Assembler, Belt, Recipe

# Belt item throughput (items/s, both lanes) = tiles/tick * 60 ticks * 8
# item-slots per tile. Yellow belt: 0.03125 * 480 == 15/s.
_BELT_ITEMS_PER_TILE_SECOND = 480.0
_DEFAULT_CRAFT_TIME = 0.5  # Factorio's default energy_required when omitted.

_ENERGY_UNITS = {"": 1e-3, "k": 1.0, "m": 1e3, "g": 1e6}  # -> kW, from W/kW/MW/GW


def _parse_energy_kw(value: str | None) -> float:
    """Parse an energy string like ``"150kW"`` / ``"1.5MW"`` into kilowatts."""
    if not value:
        return 0.0
    m = re.match(r"^\s*([0-9.]+)\s*([kKmMgG]?)[wWjJ]", str(value))
    if not m:
        return 0.0
    return float(m.group(1)) * _ENERGY_UNITS[m.group(2).lower()]


def _is_fluid(entry: object) -> bool:
    return isinstance(entry, dict) and entry.get("type") == "fluid"


def _entry_name_count(entry: object) -> tuple[str, float]:
    """Normalize one ingredient/product entry to ``(item_name, count)``."""
    if isinstance(entry, dict):
        amount = entry.get("amount")
        if amount is None:  # probabilistic result: use the mean of the range
            lo = entry.get("amount_min", 0)
            hi = entry.get("amount_max", 0)
            amount = (lo + hi) / 2.0
        prob = entry.get("probability", 1.0)
        return entry["name"], float(amount) * float(prob)
    name, count = entry  # ["name", count] pair form
    return name, float(count)


def _normalize_recipe(name: str, raw: dict) -> Recipe | None:
    """Convert one raw prototype into a :class:`Recipe`, or ``None`` if it can't
    be represented as an item-only crafting recipe (e.g. it uses fluids)."""
    body = raw.get("normal", raw)  # collapse the difficulty split
    if "ingredients" not in body and "results" not in body and "result" not in body:
        return None

    ingredients: dict[str, float] = {}
    for entry in body.get("ingredients", []):
        if _is_fluid(entry):
            return None
        item, count = _entry_name_count(entry)
        ingredients[item] = ingredients.get(item, 0.0) + count

    products: dict[str, float] = {}
    if "results" in body:
        for entry in body["results"]:
            if _is_fluid(entry):
                return None
            item, count = _entry_name_count(entry)
            products[item] = products.get(item, 0.0) + count
    else:
        result = body.get("result")
        if result is None:
            return None
        products[result] = float(body.get("result_count", 1))

    if not products:
        return None

    time = float(body.get("energy_required", raw.get("energy_required", _DEFAULT_CRAFT_TIME)))
    category = raw.get("category", body.get("category", "crafting"))
    return Recipe(
        name=name,
        ingredients=ingredients,
        products=products,
        time=time,
        category=category,
    )


def load_recipes() -> dict[str, Recipe]:
    """All item-only (fluid-free) crafting recipes from the pinned data."""
    out: dict[str, Recipe] = {}
    for name, raw in _recipes.raw.items():
        recipe = _normalize_recipe(name, raw)
        if recipe is not None:
            out[name] = recipe
    return out


def load_assemblers() -> dict[str, Assembler]:
    """All ``assembling-machine`` prototypes (crafting speed, modules, power)."""
    out: dict[str, Assembler] = {}
    for name, raw in _entities.raw.items():
        if raw.get("type") != "assembling-machine":
            continue
        # Module slots moved to a top-level field in 2.0; 1.1 nested it under
        # ``module_specification``.
        module_slots = int(
            raw.get("module_slots")
            or (raw.get("module_specification") or {}).get("module_slots", 0)
        )
        out[name] = Assembler(
            name=name,
            crafting_speed=float(raw.get("crafting_speed", 1.0)),
            categories=frozenset(raw.get("crafting_categories", ["crafting"])),
            module_slots=module_slots,
            energy_kw=_parse_energy_kw(raw.get("energy_usage")),
        )
    return out


def load_belts() -> dict[str, Belt]:
    """Transport-belt tiers, each paired with its underground belt + reach."""
    out: dict[str, Belt] = {}
    for name, raw in _entities.raw.items():
        if raw.get("type") != "transport-belt":
            continue
        ug_name = raw.get("related_underground_belt")
        ug = _entities.raw.get(ug_name, {}) if ug_name else {}
        out[name] = Belt(
            name=name,
            throughput=float(raw.get("speed", 0.0)) * _BELT_ITEMS_PER_TILE_SECOND,
            underground_name=ug_name,
            underground_max_distance=int(ug.get("max_distance", 0)),
        )
    return out


def inserter_reach(name: str, default: int = 1) -> int:
    """Reach in tiles, read from the prototype pickup offset."""
    raw = _entities.raw.get(name, {})
    pickup = raw.get("pickup_position")
    if not pickup:
        return default
    return max(1, round(max(abs(pickup[0]), abs(pickup[1]))))
