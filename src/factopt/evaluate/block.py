"""Analytical model of a belt-based single-product block.

Two responsibilities:

1. :func:`requirements` — given a solved :class:`ProductionPlan`, a belt tier and
   an inserter type, compute the *bill of throughput resources*: how many belts
   each item flow needs, how many inserters each machine needs to stay fed and
   drained, plus power and a footprint lower bound. This is the BOM that the
   placement stage consumes.

2. :func:`bottleneck` — given how much was actually *provisioned* (e.g. what a
   placed/routed layout ended up with), compute the achievable throughput as a
   fraction of target and identify the binding constraint. This is the scoring /
   validation function.

Modeling assumptions (documented because they bound accuracy):

* Flows are aggregated per recipe line and assumed evenly distributed across the
  line's machines. This is exact for a balanced block and a good approximation
  otherwise; a per-machine flow solver (or simulation) replaces it later.
* Belt throughput is treated as a single capacity number per item flow. Lane
  imbalance and splitter behavior are out of scope for v1.
* Inserter power is not yet modeled (see Inserter.energy_kw); only machine power
  is reported, which dominates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.ratios.solver import ProductionPlan

# Assemblers are 3x3 in vanilla; used for the footprint lower bound.
_DEFAULT_MACHINE_TILES = 9


@dataclass(frozen=True)
class BeltReq:
    """Belts needed to carry one item's dominant flow."""

    item: str
    flow_per_sec: float
    belts_exact: float
    belts: int


@dataclass(frozen=True)
class InserterReq:
    """Inserters needed at one recipe's machines to move one item.

    ``direction`` is "in" (belt/chest -> machine) or "out" (machine -> belt).
    Counts are per single machine and for the whole line.
    """

    recipe: str
    item: str
    direction: str
    flow_per_machine_per_sec: float
    per_machine: int
    total: int


@dataclass
class BlockRequirements:
    plan: ProductionPlan
    belt: str
    inserter: str
    belt_reqs: list[BeltReq]
    inserter_reqs: list[InserterReq]
    machine_power_kw: float
    machine_area_tiles: int

    @property
    def total_inserters(self) -> int:
        return sum(r.total for r in self.inserter_reqs)

    @property
    def total_belts(self) -> int:
        return sum(r.belts for r in self.belt_reqs)

    def __str__(self) -> str:
        out = [
            f"Requirements for {self.plan.rate:g}/s {self.plan.target}"
            f" ({self.belt} + {self.inserter}):",
            f"  belts: {self.total_belts}  inserters: {self.total_inserters}"
            f"  machines: {self.plan.total_machines}",
            f"  machine power: {self.machine_power_kw:.0f} kW"
            f"  machine area (lower bound): {self.machine_area_tiles} tiles",
        ]
        for b in sorted(self.belt_reqs, key=lambda x: x.item):
            out.append(f"    belt  {b.belts:>2} x {b.item:<18} ({b.flow_per_sec:.1f}/s)")
        for i in sorted(self.inserter_reqs, key=lambda x: (x.recipe, x.direction, x.item)):
            out.append(
                f"    ins   {i.total:>3} ({i.per_machine}/machine) "
                f"{i.direction:<3} {i.item:<18} @ {i.recipe}"
            )
        return "\n".join(out)


def _per_machine_crafts(plan: ProductionPlan, db: Database, recipe_name: str) -> float:
    speed = db.assemblers[plan.assembler].crafting_speed
    return speed / db.recipes[recipe_name].time


def requirements(
    plan: ProductionPlan,
    db: Database,
    belt: str = "transport-belt",
    inserter: str = "fast-inserter",
    direct_items: frozenset[str] = frozenset(),
) -> BlockRequirements:
    """Compute the throughput resource bill for a plan.

    Items in ``direct_items`` are moved by **direct insertion** (machine ->
    machine), not belts: they need no belt lane, and a single transfer inserter
    does the work of the producer's "out" plus the consumer's "in" inserter (so
    roughly half the inserters of the belt-fed equivalent).
    """
    if belt not in db.belts:
        raise ValueError(f"unknown belt {belt!r}")
    if inserter not in db.inserters:
        raise ValueError(f"unknown inserter {inserter!r}")

    belt_tp = db.belts[belt].throughput
    ins_rate = db.inserters[inserter].rate

    # Belts: one entry per non-direct item that flows, sized to its dominant flow.
    belt_reqs: list[BeltReq] = []
    for item, flow in plan.flows.items():
        if item in direct_items:
            continue
        dominant = max(flow.produced_per_sec, flow.consumed_per_sec)
        if dominant <= 0:
            continue
        exact = dominant / belt_tp
        belt_reqs.append(
            BeltReq(
                item=item, flow_per_sec=dominant, belts_exact=exact, belts=math.ceil(exact - 1e-9)
            )
        )

    # Inserters: per machine, one group per (recipe, item, direction). Direct
    # items are handled separately below as transfer inserters.
    inserter_reqs: list[InserterReq] = []
    for line in plan.lines:
        recipe = db.recipes[line.recipe]
        pmc = _per_machine_crafts(plan, db, line.recipe)
        for item, count in recipe.ingredients.items():
            if item in direct_items:
                continue
            flow = count * pmc
            per = math.ceil(flow / ins_rate - 1e-9)
            inserter_reqs.append(
                InserterReq(line.recipe, item, "in", flow, per, per * line.machines)
            )
        for item, count in recipe.products.items():
            if item in direct_items:
                continue
            flow = count * pmc
            per = math.ceil(flow / ins_rate - 1e-9)
            inserter_reqs.append(
                InserterReq(line.recipe, item, "out", flow, per, per * line.machines)
            )

    # Transfer inserters for direct-inserted items (one per edge, sized to the
    # item's whole block flow).
    for item in sorted(direct_items):
        flow = plan.flows.get(item)
        if flow is None:
            continue
        total_flow = max(flow.produced_per_sec, flow.consumed_per_sec)
        if total_flow <= 0:
            continue
        n = math.ceil(total_flow / ins_rate - 1e-9)
        inserter_reqs.append(InserterReq("(transfer)", item, "transfer", total_flow, n, n))

    machine_power = sum(
        db.assemblers[plan.assembler].energy_kw * line.machines for line in plan.lines
    )
    machine_area = sum(
        db.assemblers[plan.assembler].width * db.assemblers[plan.assembler].height * line.machines
        for line in plan.lines
    )

    return BlockRequirements(
        plan=plan,
        belt=belt,
        inserter=inserter,
        belt_reqs=belt_reqs,
        inserter_reqs=inserter_reqs,
        machine_power_kw=machine_power,
        machine_area_tiles=machine_area,
    )


@dataclass(frozen=True)
class LineThroughput:
    """Per-line achievable craft fraction and which resource binds it."""

    recipe: str
    fraction: float  # achievable crafts / nominal crafts, clamped to [0, 1]
    limiter: str  # "machines" | "belt:<item>" | "inserter:<dir>:<item>"


@dataclass
class Bottleneck:
    """Result of scoring a provisioning against a plan."""

    plan: ProductionPlan
    fraction: float  # block-wide achievable / target, clamped to [0, 1]
    achievable_rate: float
    limiter: str
    per_line: list[LineThroughput] = field(default_factory=list)

    @property
    def meets_target(self) -> bool:
        return self.fraction >= 1.0 - 1e-9


def bottleneck(
    plan: ProductionPlan,
    db: Database,
    belt: str = "transport-belt",
    inserter: str = "fast-inserter",
    belts_provided: dict[str, int] | None = None,
    inserters_provided: dict[tuple[str, str, str], int] | None = None,
    direct_items: frozenset[str] = frozenset(),
) -> Bottleneck:
    """Score achievable throughput given provisioning.

    ``belts_provided`` maps item -> belt count; ``inserters_provided`` maps
    (recipe, item, direction) -> inserter count. Anything omitted defaults to the
    fully-provisioned requirement, so calling with no provisioning yields the
    target rate (the validation baseline).

    ``direct_items`` are direct-inserted (no belt): their throughput is limited
    by transfer-inserter capacity, looked up under key (``"(transfer)"``, item,
    ``"transfer"``).
    """
    req = requirements(plan, db, belt=belt, inserter=inserter, direct_items=direct_items)
    belt_tp = db.belts[belt].throughput
    ins_rate = db.inserters[inserter].rate

    belts_provided = belts_provided or {}
    inserters_provided = inserters_provided or {}

    # Default provisioning = requirement, so unspecified resources never bind.
    belt_default = {b.item: b.belts for b in req.belt_reqs}
    ins_default = {(i.recipe, i.item, i.direction): i.per_machine for i in req.inserter_reqs}

    # Belt supply per item (shared across the whole block).
    belt_supply = {
        item: belts_provided.get(item, belt_default.get(item, 0)) * belt_tp for item in belt_default
    }

    # Transfer-inserter supply (items/s) per direct item.
    direct_supply = {
        item: inserters_provided.get(
            ("(transfer)", item, "transfer"),
            ins_default.get(("(transfer)", item, "transfer"), 0),
        )
        * ins_rate
        for item in direct_items
    }

    per_line: list[LineThroughput] = []
    for line in plan.lines:
        recipe = db.recipes[line.recipe]
        pmc = _per_machine_crafts(plan, db, line.recipe)
        # Score against the craft rate *required* to hit target, not the nominal
        # machine capacity: machine counts are rounded up, so nominal capacity
        # exceeds demand and would otherwise make a healthy block look starved.
        required_crafts = line.crafts_per_sec

        frac = float("inf")
        limiter = "none"

        def consider(cap_crafts: float, name: str) -> None:
            nonlocal frac, limiter
            f = cap_crafts / required_crafts if required_crafts > 0 else float("inf")
            if f < frac:
                frac = f
                limiter = name

        # Installed machine capacity is itself a constraint.
        consider(pmc * line.machines, "machines")

        # Inserter limits (per machine -> scaled to the line). Direct items use
        # the shared transfer constraint instead of per-machine in/out inserters.
        for item, count in recipe.ingredients.items():
            if item in direct_items:
                consider(direct_supply[item] / count, f"direct:{item}")
                continue
            per = inserters_provided.get(
                (line.recipe, item, "in"), ins_default[(line.recipe, item, "in")]
            )
            cap = per * ins_rate * line.machines / count
            consider(cap, f"inserter:in:{item}")
        for item, count in recipe.products.items():
            if item in direct_items:
                consider(direct_supply[item] / count, f"direct:{item}")
                continue
            per = inserters_provided.get(
                (line.recipe, item, "out"), ins_default[(line.recipe, item, "out")]
            )
            cap = per * ins_rate * line.machines / count
            consider(cap, f"inserter:out:{item}")

        # Belt limits (block-shared supply / per-craft coefficient).
        for item, count in recipe.ingredients.items():
            if item in belt_supply:
                consider(belt_supply[item] / count, f"belt:{item}")
        for item, count in recipe.products.items():
            if item in belt_supply:
                consider(belt_supply[item] / count, f"belt:{item}")

        per_line.append(
            LineThroughput(recipe=line.recipe, fraction=min(frac, 1.0), limiter=limiter)
        )

    worst = min(per_line, key=lambda x: x.fraction) if per_line else None
    fraction = min((p.fraction for p in per_line), default=1.0)
    fraction = max(0.0, min(fraction, 1.0))
    return Bottleneck(
        plan=plan,
        fraction=fraction,
        achievable_rate=fraction * plan.rate,
        limiter=worst.limiter if worst else "none",
        per_line=per_line,
    )
