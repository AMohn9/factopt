"""End-to-end MVP: synthesize a tight green-circuit block.

This is a deliberately simple, deterministic generator (no search) that wires
together the rest of the pipeline into a working vertical slice:

    solve_ratios -> shared-lane bus layout -> evaluate -> blueprint string

It builds the classic compact green-circuit pattern, scaled by the solved
machine counts:

    copper-plate lane  ───────────────────────────
       [ inserters ]   pick plate -> cable machines
    [ COPPER-CABLE machine row ]
       [ inserters ]   cable machines drop -> cable lane
    copper-cable lane  ───────────────────────────   (shared)
       [ inserters ]   EC machines pick cable up
    [ ELECTRONIC-CIRCUIT machine row ]
       [ inserters ]   EC out (normal) + iron in (long-handed reaches the
    electronic-circuit lane ──────────────────────    iron lane below)
    iron-plate lane    ───────────────────────────

The shared cable lane is the no-splitter trick: cable machines (left) drop onto
it, EC machines (right) grab from it as cable flows east. Long-handed inserters
let the EC row reach a second bottom lane.

Scope: any supported 2-level chain (product = one intermediate + one raw; the
intermediate = one raw), e.g. green circuits or red science. The chain roles are
derived from the recipe graph. Single belt lane per item with the tier
auto-selected; rates above one lane's capacity tile into independent sub-blocks.
Inserter facing follows the (in-game-verified) pickup convention.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from factopt.codec import encode
from factopt.data.database import Database
from factopt.evaluate import Bottleneck, BlockRequirements, bottleneck, requirements
from factopt.model.blueprint import EAST, NORTH, SOUTH, Blueprint, Entity, Position
from factopt.ratios.solver import ProductionPlan, solve_ratios

_TARGET = "electronic-circuit"
_ASSEMBLER = "assembling-machine-2"
_BELT_TIERS = ["transport-belt", "fast-transport-belt", "express-transport-belt"]


@dataclass
class SynthesisResult:
    plan: ProductionPlan
    requirements: BlockRequirements
    validation: Bottleneck
    blueprint: Blueprint
    blueprint_string: str
    width: int
    height: int
    blocks: int = 1

    @property
    def area(self) -> int:
        return self.width * self.height

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in self.blueprint.entities:
            out[e.name] = out.get(e.name, 0) + 1
        return out

    def summary(self) -> str:
        c = self.counts()
        n_inserters = sum(v for k, v in c.items() if "inserter" in k)
        n_belts = sum(v for k, v in c.items() if "belt" in k)
        n_machines = c.get(_ASSEMBLER, 0)
        return (
            f"{self.plan.rate:g}/s {self.plan.target} ({self.blocks} sub-block(s))\n"
            f"  belt tier: {self.requirements.belt}\n"
            f"  machines: {n_machines}"
            f"  inserters: {n_inserters}  belts: {n_belts}\n"
            f"  footprint: {self.width} x {self.height} = {self.area} tiles\n"
            f"  meets target: {self.validation.meets_target}"
            f" ({self.validation.achievable_rate:g}/s, limiter={self.validation.limiter})"
        )


def _select_belt(plan: ProductionPlan, db: Database, belt: str | None) -> str:
    """Pick the cheapest belt tier where every item flow fits a single lane."""
    max_flow = max(max(f.produced_per_sec, f.consumed_per_sec) for f in plan.flows.values())
    tiers = [belt] if belt else _BELT_TIERS
    for name in tiers:
        if name not in db.belts:
            raise ValueError(f"unknown belt {name!r}")
        if db.belts[name].throughput >= max_flow - 1e-9:
            return name
    raise ValueError(
        f"flow {max_flow:g}/s exceeds a single {tiers[-1]} lane; "
        "multi-lane layouts are not supported by the MVP generator yet"
    )


@dataclass(frozen=True)
class _Chain:
    """A supported 2-level chain: product made from one intermediate + one raw,
    the intermediate made from one raw."""

    product: str
    intermediate: str
    raw1: str  # raw consumed by the intermediate
    raw2: str  # raw consumed by the product (besides the intermediate)
    raw1_count: float  # per intermediate craft
    int_out_count: float
    int_in_count: float  # intermediate per product craft
    raw2_count: float
    prod_out_count: float


def _derive_chain(target: str, db: Database) -> _Chain:
    """Infer the chain roles from the recipe graph, validating the supported
    2-level shape (product = 1 intermediate + 1 raw; intermediate = 1 raw)."""
    prod = db.recipe_for(target)
    if prod is None:
        raise ValueError(f"no recipe for {target!r}")
    intermediates = [i for i in prod.ingredients if not db.is_raw(i)]
    raws = [i for i in prod.ingredients if db.is_raw(i)]
    if len(intermediates) != 1 or len(raws) != 1:
        raise ValueError(
            f"{target!r} is not a supported 2-level chain "
            f"(intermediates={intermediates}, raws={raws})"
        )
    intermediate, raw2 = intermediates[0], raws[0]
    inter = db.recipe_for(intermediate)
    int_raws = [i for i in inter.ingredients if db.is_raw(i)]
    if len(int_raws) != 1 or any(not db.is_raw(i) for i in inter.ingredients):
        raise ValueError(f"intermediate {intermediate!r} is not a single-raw recipe")
    raw1 = int_raws[0]
    return _Chain(
        product=target,
        intermediate=intermediate,
        raw1=raw1,
        raw2=raw2,
        raw1_count=inter.ingredients[raw1],
        int_out_count=inter.products[intermediate],
        int_in_count=prod.ingredients[intermediate],
        raw2_count=prod.ingredients[raw2],
        prod_out_count=prod.products[target],
    )


def _synthesize_single(
    rate: float,
    db: Database,
    target: str,
    belt: str | None,
    inserter: str,
    long_inserter: str,
) -> tuple[list[Entity], int, int, ProductionPlan, str]:
    """Build one single-lane block for a 2-level chain. Returns
    (entities, width, height, plan, belt_name)."""
    chain = _derive_chain(target, db)
    plan = solve_ratios(target, rate, db, assembler=_ASSEMBLER)
    int_recipe = db.recipe_for(chain.intermediate).name
    prod_recipe = db.recipe_for(chain.product).name
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    n_int, n_prod = counts[int_recipe], counts[prod_recipe]
    belt_name = _select_belt(plan, db, belt)

    ins_rate = db.inserters[inserter].rate
    long_rate = db.inserters[long_inserter].rate
    speed = db.assemblers[_ASSEMBLER].crafting_speed
    pmc_int = speed / db.recipes[int_recipe].time
    pmc_prod = speed / db.recipes[prod_recipe].time

    def n_ins(count: float, pmc: float, rate_: float) -> int:
        return max(1, math.ceil(count * pmc / rate_ - 1e-9))

    n_raw1_in = n_ins(chain.raw1_count, pmc_int, ins_rate)  # raw1 -> intermediate
    n_int_out = n_ins(chain.int_out_count, pmc_int, ins_rate)  # intermediate -> lane
    n_int_in = n_ins(chain.int_in_count, pmc_prod, ins_rate)  # lane -> product
    n_raw2_in = n_ins(chain.raw2_count, pmc_prod, long_rate)  # raw2 -> product (long)
    n_prod_out = n_ins(chain.prod_out_count, pmc_prod, ins_rate)  # product -> lane

    # Each machine side has 3 inserter slots; bail if a side is over-subscribed.
    if max(n_raw1_in, n_int_out, n_int_in, n_prod_out + n_raw2_in) > 3:
        raise ValueError(
            f"{target!r} needs more than 3 inserters on a machine side at "
            f"{rate:g}/s; multi-row I/O not supported by this generator yet"
        )

    width = max(3 * n_int, 3 * n_prod, 1)

    # Row y-coordinates (top to bottom): raw1 lane / intermediate row / shared
    # intermediate lane / product row / product lane / raw2 lane.
    Y_RAW1 = 0
    Y_INT_TOP_INS = 1
    Y_INT = 2  # machine rows 2..4
    Y_INT_BOT_INS = 5
    Y_INT_LANE = 6
    Y_PROD_TOP_INS = 7
    Y_PROD = 8  # machine rows 8..10
    Y_PROD_BOT_INS = 11
    Y_PROD_LANE = 12
    Y_RAW2 = 13
    height = 14

    entities: list[Entity] = []

    def add_belt(x: int, y: int) -> None:
        entities.append(
            Entity(name=belt_name, position=Position(x + 0.5, y + 0.5), direction=EAST)
        )  # items flow left->right

    def add_machine(x: int, y: int, recipe: str) -> None:
        entities.append(Entity(name=_ASSEMBLER, position=Position(x + 1.5, y + 1.5), recipe=recipe))

    def add_inserter(x: int, y: int, pickup: int, name: str = inserter) -> None:
        # Blueprint quirk: an inserter's ``direction`` points toward the tile it
        # PICKS UP from (opposite the in-game arrow / its drop side). Verified.
        entities.append(Entity(name=name, position=Position(x + 0.5, y + 0.5), direction=pickup))

    for x in range(width):
        add_belt(x, Y_RAW1)
        add_belt(x, Y_INT_LANE)
        add_belt(x, Y_PROD_LANE)
        add_belt(x, Y_RAW2)

    # Intermediate machines: raw1 in from the lane above, intermediate out below.
    for i in range(n_int):
        mx = 3 * i
        add_machine(mx, Y_INT, int_recipe)
        for k in range(n_raw1_in):
            add_inserter(mx + k, Y_INT_TOP_INS, NORTH)
        for k in range(n_int_out):
            add_inserter(mx + k, Y_INT_BOT_INS, NORTH)

    # Product machines: intermediate in from the shared lane above; product out
    # plus raw2 in (long-handed, reaching the raw2 lane below the product lane).
    for j in range(n_prod):
        mx = 3 * j
        add_machine(mx, Y_PROD, prod_recipe)
        for k in range(n_int_in):
            add_inserter(mx + k, Y_PROD_TOP_INS, NORTH)
        slot = 0
        for _ in range(n_prod_out):
            add_inserter(mx + slot, Y_PROD_BOT_INS, NORTH)
            slot += 1
        for _ in range(n_raw2_in):
            add_inserter(mx + slot, Y_PROD_BOT_INS, SOUTH, name=long_inserter)
            slot += 1

    return entities, width, height, plan, belt_name


_BLOCK_GAP = 2  # empty columns between tiled sub-blocks


def _max_single_rate(target: str, db: Database) -> float:
    """Largest rate one single-lane block can carry: the fastest belt divided by
    the chain's heaviest per-rate item-flow coefficient."""
    probe = solve_ratios(target, 1.0, db, assembler=_ASSEMBLER)
    coeff = max(max(f.produced_per_sec, f.consumed_per_sec) for f in probe.flows.values())
    fastest = max(b.throughput for b in db.belts.values())
    return fastest / coeff


def synthesize(
    rate: float,
    db: Database,
    target: str = _TARGET,
    belt: str | None = None,
    inserter: str = "fast-inserter",
    long_inserter: str = "long-handed-inserter",
    label: str | None = None,
) -> SynthesisResult:
    """Synthesize a complete block producing ``rate`` items/s of ``target``.

    Handles any supported 2-level chain (product = one intermediate + one raw).
    For rates above a single lane's capacity the block is tiled into K
    independent single-lane sub-blocks laid side by side. This is deliberately
    loose (no sharing between sub-blocks); compaction is a separate step.
    """
    if rate <= 0:
        raise ValueError("rate must be positive")
    max_single = _max_single_rate(target, db)
    n_blocks = max(1, math.ceil(rate / max_single - 1e-9))
    sub_rate = rate / n_blocks

    entities: list[Entity] = []
    x_offset = 0
    total_width = 0
    height = 0
    sub_belt = ""
    for _ in range(n_blocks):
        ents, w, h, _plan, sub_belt = _synthesize_single(
            sub_rate, db, target, belt, inserter, long_inserter
        )
        for e in ents:
            entities.append(
                Entity(
                    name=e.name,
                    position=Position(e.position.x + x_offset, e.position.y),
                    direction=e.direction,
                    recipe=e.recipe,
                    extra=dict(e.extra),
                )
            )
        x_offset += w + _BLOCK_GAP
        total_width = x_offset - _BLOCK_GAP
        height = max(height, h)

    label = label or f"{target}-{rate:g}ps"
    blueprint = Blueprint(label=label, entities=entities)

    # Aggregate plan at the full rate (machine counts), and validate per sub-block
    # (each meets sub_rate -> the tiled whole meets rate).
    plan = solve_ratios(target, rate, db, assembler=_ASSEMBLER)
    sub_plan = solve_ratios(target, sub_rate, db, assembler=_ASSEMBLER)
    req = requirements(plan, db, belt=sub_belt, inserter=inserter)
    sub_validation = bottleneck(sub_plan, db, belt=sub_belt, inserter=inserter)
    validation = Bottleneck(
        plan=plan,
        fraction=sub_validation.fraction,
        achievable_rate=sub_validation.achievable_rate * n_blocks,
        limiter=sub_validation.limiter,
        per_line=sub_validation.per_line,
    )

    return SynthesisResult(
        plan=plan,
        requirements=req,
        validation=validation,
        blueprint=blueprint,
        blueprint_string=encode(blueprint),
        width=total_width,
        height=height,
        blocks=n_blocks,
    )
