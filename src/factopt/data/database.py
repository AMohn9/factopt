"""A container bundling recipes and entity prototypes for one ruleset."""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.model.game import Assembler, Belt, Inserter, Recipe


@dataclass
class Database:
    recipes: dict[str, Recipe] = field(default_factory=dict)
    assemblers: dict[str, Assembler] = field(default_factory=dict)
    belts: dict[str, Belt] = field(default_factory=dict)
    inserters: dict[str, Inserter] = field(default_factory=dict)
    # Items with no producing recipe in this DB are treated as freely supplied
    # "raw" inputs by the ratio solver (e.g. iron-plate, copper-plate).
    raw_items: frozenset[str] = field(default_factory=frozenset)

    def recipe_for(self, item: str) -> Recipe | None:
        """Return the (single) recipe whose primary product is ``item``.

        v1 assumes one canonical recipe per item. Recipe *selection* (oil, etc.)
        is a later MILP concern; for the electronics subset this is unambiguous.
        """
        for r in self.recipes.values():
            if r.products.get(item, 0.0) > 0.0:
                return r
        return None

    def is_raw(self, item: str) -> bool:
        return item in self.raw_items or self.recipe_for(item) is None
