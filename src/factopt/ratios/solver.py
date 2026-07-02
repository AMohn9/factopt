"""Solve recipe ratios for a single-product block via linear programming.

Given a target item and rate (items/s), determine how many crafts/s of each
recipe are required, then convert to (fractional and integer) machine counts for
a chosen assembler. Raw items are treated as freely supplied inputs.

The LP is small and, for a single recipe per item, fully determined; the LP
framing is kept so that recipe *selection* (multiple producers of one item) can
be added later without restructuring.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pulp

from factopt.data.database import Database


@dataclass
class MachineLine:
    """One recipe's machine requirement within a plan."""

    recipe: str
    crafts_per_sec: float
    machines_exact: float
    machines: int  # ceil(machines_exact)


@dataclass
class ItemFlow:
    """Aggregate flow of one item across the whole block."""

    item: str
    produced_per_sec: float
    consumed_per_sec: float
    is_raw: bool

    @property
    def net_per_sec(self) -> float:
        return self.produced_per_sec - self.consumed_per_sec

    def belts(self, belt_throughput: float) -> float:
        """Number of full belts (of the given throughput) needed to carry the
        larger of this item's production/consumption flows."""
        flow = max(self.produced_per_sec, self.consumed_per_sec)
        return flow / belt_throughput


@dataclass
class ProductionPlan:
    target: str
    rate: float
    assembler: str
    lines: list[MachineLine]
    flows: dict[str, ItemFlow]

    @property
    def total_machines(self) -> int:
        return sum(line.machines for line in self.lines)

    def raw_inputs(self) -> dict[str, float]:
        """Raw item -> consumption rate (items/s)."""
        return {
            f.item: f.consumed_per_sec
            for f in self.flows.values()
            if f.is_raw and f.consumed_per_sec > 0
        }

    def __str__(self) -> str:
        lines = [
            f"Plan: {self.rate:g}/s {self.target} using {self.assembler}",
            f"  machines: {self.total_machines} total",
        ]
        for ln in self.lines:
            lines.append(
                f"    {ln.machines:>3} x {ln.recipe:<22} "
                f"({ln.machines_exact:.2f} exact, {ln.crafts_per_sec:.3f} crafts/s)"
            )
        raws = self.raw_inputs()
        if raws:
            lines.append("  raw inputs:")
            for item, r in sorted(raws.items()):
                lines.append(f"    {r:8.3f}/s {item}")
        return "\n".join(lines)


def _required_recipes(target: str, db: Database) -> dict[str, "object"]:
    """Walk the dependency tree from ``target``, collecting recipes until raw
    items are reached. Returns recipe_name -> Recipe."""
    needed: dict[str, object] = {}
    stack = [target]
    seen: set[str] = set()
    while stack:
        item = stack.pop()
        if item in seen or db.is_raw(item):
            continue
        seen.add(item)
        recipe = db.recipe_for(item)
        if recipe is None:
            continue
        needed[recipe.name] = recipe
        for ing in recipe.ingredients:
            if ing not in seen:
                stack.append(ing)
    return needed


def solve_ratios(
    target: str,
    rate: float,
    db: Database,
    assembler: str = "assembling-machine-2",
) -> ProductionPlan:
    """Compute a production plan for ``rate`` items/s of ``target``."""
    if rate <= 0:
        raise ValueError("rate must be positive")
    if db.is_raw(target):
        raise ValueError(f"{target!r} is a raw item with no recipe to optimize")
    if assembler not in db.assemblers:
        raise ValueError(f"unknown assembler {assembler!r}")

    recipes = _required_recipes(target, db)
    if not recipes:
        raise ValueError(f"no recipe found for {target!r}")

    prob = pulp.LpProblem("ratios", pulp.LpMinimize)

    # Decision variables: crafts/sec for each recipe.
    r = {name: pulp.LpVariable(f"r_{name}", lowBound=0) for name in recipes}

    # Collect every item touched by the chosen recipes.
    items: set[str] = set()
    for rec in recipes.values():
        items.update(rec.ingredients)
        items.update(rec.products)

    # Flow-balance constraints for non-raw items.
    for item in items:
        if db.is_raw(item):
            continue
        net = pulp.lpSum(rec.net(item) * r[name] for name, rec in recipes.items())
        demand = rate if item == target else 0.0
        prob += net >= demand, f"balance_{item}"

    # Objective: minimize total machine-time (proportional to machine count).
    speed = db.assemblers[assembler].crafting_speed
    prob += pulp.lpSum(rec.time / speed * r[name] for name, rec in recipes.items())

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"LP not optimal: {pulp.LpStatus[status]}")

    lines: list[MachineLine] = []
    for name, rec in recipes.items():
        crafts = float(r[name].value() or 0.0)
        machines_exact = crafts * rec.time / speed
        lines.append(
            MachineLine(
                recipe=name,
                crafts_per_sec=crafts,
                machines_exact=machines_exact,
                machines=math.ceil(machines_exact - 1e-9),
            )
        )
    lines.sort(key=lambda ln: ln.recipe)

    # Aggregate item flows from the solved craft rates.
    produced: dict[str, float] = {}
    consumed: dict[str, float] = {}
    for name, rec in recipes.items():
        crafts = float(r[name].value() or 0.0)
        for it, c in rec.products.items():
            produced[it] = produced.get(it, 0.0) + c * crafts
        for it, c in rec.ingredients.items():
            consumed[it] = consumed.get(it, 0.0) + c * crafts

    flows: dict[str, ItemFlow] = {}
    for it in items:
        flows[it] = ItemFlow(
            item=it,
            produced_per_sec=produced.get(it, 0.0),
            consumed_per_sec=consumed.get(it, 0.0),
            is_raw=db.is_raw(it),
        )

    return ProductionPlan(
        target=target,
        rate=rate,
        assembler=assembler,
        lines=lines,
        flows=flows,
    )
