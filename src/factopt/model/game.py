"""Typed game-data structures (recipes, machines, belts, inserters).

Numeric values follow vanilla Factorio 2.0. Times are in seconds at crafting
speed 1.0; counts are per single craft.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recipe:
    """A crafting recipe.

    ``ingredients`` and ``products`` map item name -> count per craft.
    ``time`` is the base crafting time in seconds (energy_required) at speed 1.0.
    ``category`` gates which machines can craft it (e.g. "crafting",
    "advanced-crafting"); fluid categories are intentionally excluded for v1.
    """

    name: str
    ingredients: dict[str, float]
    products: dict[str, float]
    time: float
    category: str = "crafting"

    def net(self, item: str) -> float:
        """Net output of ``item`` per craft (products minus ingredients)."""
        return self.products.get(item, 0.0) - self.ingredients.get(item, 0.0)


@dataclass(frozen=True)
class Assembler:
    """A crafting machine."""

    name: str
    crafting_speed: float
    # Footprint in tiles (width, height); assemblers are square in vanilla.
    width: int = 3
    height: int = 3
    # Recipe categories this machine can craft.
    categories: frozenset[str] = field(default_factory=lambda: frozenset({"crafting"}))
    module_slots: int = 0
    energy_kw: float = 0.0


@dataclass(frozen=True)
class Belt:
    """A transport belt tier."""

    name: str
    # Items per second carried by a full belt (both lanes combined).
    throughput: float
    # Matching underground-belt prototype, if any.
    underground_name: str | None = None
    # Prototype ``max_distance``: the maximum coordinate separation between the
    # two underground ends. Vanilla values are 5 / 7 / 9 for yellow / red /
    # blue, which lets them span 4 / 6 / 8 obstacle tiles respectively.
    underground_max_distance: int = 0


@dataclass(frozen=True)
class Inserter:
    """An inserter type."""

    name: str
    # Approximate items/s moving a stack-size-1 hand at full health, no bonuses.
    # This is a coarse placeholder; the analytical evaluator will refine it.
    rate: float
    # Reach in tiles from the inserter tile to the pickup/dropoff tile.
    reach: int = 1
