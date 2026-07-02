"""Vanilla Factorio game data, sourced from Draftsman (defaults to 2.0).

Recipes, assemblers, and belts are loaded from Draftsman's prototype data (see
:mod:`factopt.data.factorio`). This replaces the previously hand-maintained
electronics subset with the full fluid-free recipe set. Draftsman's default data
includes the Space Age mods, but factopt only emits base-game entities, so the
generated blueprints import into vanilla 2.0 all the same.

Two things stay curated here:

* **Inserter throughput** -- a gameplay-derived quantity (rotation + extension
  speed, hand stack size, bonuses), not a clean prototype field.
* **Raw items** -- the boundary the ratio solver stops at. With full data,
  plates *do* have smelting recipes, so we must explicitly declare which items
  are supplied externally rather than crafted inside a block.
"""

from __future__ import annotations

from factopt.data.database import Database
from factopt.data.factorio import (
    inserter_reach,
    load_assemblers,
    load_belts,
    load_recipes,
)
from factopt.model.game import Inserter

# --- Inserters (curated items/s; refined later by the evaluator) -------------

_INSERTER_RATES = {
    "inserter": 0.83,
    "long-handed-inserter": 1.2,
    "fast-inserter": 2.31,
    "stack-inserter": 9.4,
}

_INSERTERS = [
    Inserter(name=name, rate=rate, reach=inserter_reach(name))
    for name, rate in _INSERTER_RATES.items()
]

# --- Raw items: the externally-supplied boundary the solver stops at ---------

_RAW_ITEMS = frozenset(
    {
        "iron-plate",
        "copper-plate",
        "steel-plate",
        "stone-brick",
        "stone",
        "coal",
        "wood",
        "plastic-bar",
        "sulfur",
        "battery",
    }
)


DB = Database(
    recipes=load_recipes(),
    assemblers=load_assemblers(),
    belts=load_belts(),
    inserters={i.name: i for i in _INSERTERS},
    raw_items=_RAW_ITEMS,
)
