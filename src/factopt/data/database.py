"""A container bundling recipes and entity prototypes for one ruleset."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace

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

    def with_inputs(self, items: Iterable[str]) -> "Database":
        """Return a copy of this database that treats ``items`` as freely
        supplied ("raw") inputs, on top of the naturally raw items.

        This is how a caller declares that an intermediate built elsewhere in
        the factory (e.g. green/red circuits produced in a dedicated section)
        should enter this block as an external input rather than be
        manufactured inside it. Every stage keys "is this a block boundary?"
        off :meth:`is_raw`, so adding an item here stops the ratio solver from
        expanding its recipe and makes :func:`factopt.macros.build_problem`
        give it a west-edge input connector -- no other code paths change.

        The recipes themselves are left intact (only ``raw_items`` grows), and
        the original database is not mutated. Passing no items returns ``self``.
        """
        extra = frozenset(items)
        if not extra:
            return self
        return replace(self, raw_items=self.raw_items | extra)
