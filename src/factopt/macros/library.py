"""Build the macro-cell instance for a production plan.

Turns a :class:`~factopt.ratios.solver.ProductionPlan` into:

* one **recipe-band macro** per machine line (a :func:`factopt.band.build_band`
  row, so the emission is the geometry already verified by the bus/line
  strategies), extended with a splitter fan-out when its product feeds several
  consumers so that **every net is a dedicated port-to-port belt route**;
* one **input connector** per raw item (pinned to the west edge), likewise
  fanned out per consumer;
* one **output collector** for the target (pinned to the east edge).

The result (:class:`MacroProblem`) is the master problem's input: macros to
place, nets to route, and edge pins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.band import build_band
from factopt.data.database import Database
from factopt.macros.cell import MacroCell, PortCandidate, Side
from factopt.model.blueprint import EAST, Entity, Position
from factopt.ratios.solver import ProductionPlan

_SPLITTER_OF = {
    "transport-belt": "splitter",
    "fast-transport-belt": "fast-splitter",
    "express-transport-belt": "express-splitter",
}


@dataclass(frozen=True)
class FlowNet:
    """One item flow the detailed router must realize as a belt path."""

    id: str
    item: str
    source_macro: str
    source_port: str
    sink_macro: str
    sink_port: str
    rate_per_sec: float


@dataclass
class MacroProblem:
    plan: ProductionPlan
    macros: dict[str, MacroCell] = field(default_factory=dict)
    nets: list[FlowNet] = field(default_factory=list)
    # Macro id -> blueprint edge it must touch ("west" inputs, "east" output).
    pins: dict[str, Side] = field(default_factory=dict)


def _fanout_east(
    entities: list[Entity],
    belt_name: str,
    feed_col: int,
    row: int,
    k: int,
) -> tuple[list[tuple[int, int]], int, int]:
    """Extend an EAST-flowing lane whose last belt sits at ``(feed_col - 1,
    row)`` into ``k`` separate east-edge branches via a diagonal splitter
    cascade. Appends the new entities and returns
    ``(port_tiles, width_needed, max_row)``.
    """
    if k <= 1:
        return [(feed_col - 1, row)], feed_col, row

    splitter = _SPLITTER_OF.get(belt_name, "splitter")
    end_col = feed_col + 2 * (k - 2) + 1

    def belt(x: int, y: int) -> None:
        entities.append(
            Entity(name=belt_name, position=Position(x + 0.5, y + 0.5), direction=EAST)
        )

    for i in range(k - 1):
        c = feed_col + 2 * i
        # EAST-facing splitter occupying (c, row+i) and (c, row+i+1); its
        # upper input is fed by the lane (i == 0) or the previous bridge belt.
        entities.append(
            Entity(name=splitter, position=Position(c + 0.5, row + i + 1.0), direction=EAST)
        )
        # Upper output: branch i runs east to the macro edge.
        for x in range(c + 1, end_col + 1):
            belt(x, row + i)
        if i < k - 2:
            # Lower output bridges one tile east into the next splitter.
            belt(c + 1, row + i + 1)
        else:
            # Lower output of the last splitter: branch k-1 to the edge.
            for x in range(c + 1, end_col + 1):
                belt(x, row + i + 1)

    ports = [(end_col, row + i) for i in range(k)]
    return ports, end_col + 1, row + k - 1


def _band_macro(
    recipe: str,
    n_machines: int,
    sinks: list[str],
    db: Database,
    belt: str,
    inserter: str,
    long_inserter: str,
    cap: float,
) -> MacroCell:
    band = build_band(
        recipe,
        n_machines,
        db,
        inserter=inserter,
        long_inserter=long_inserter,
        with_lane_belts=True,
        belt_name=belt,
    )
    entities = list(band.entities)
    ports: list[PortCandidate] = []

    out_slot, out_item = None, None
    for slot, a in band.lanes.items():
        if a.flow_dir == "in":
            ports.append(
                PortCandidate(
                    id=f"{a.item}-in",
                    item=a.item,
                    direction="input",
                    side="west",
                    local_position=(0, band.lane_row[slot]),
                    flow_entry_dir=EAST,
                    max_rate_per_sec=cap,
                )
            )
        else:
            out_slot, out_item = slot, a.item

    width, height = band.width, band.height
    if out_slot is not None and sinks:
        out_row = band.lane_row[out_slot]
        tiles, width_needed, max_row = _fanout_east(
            entities, belt, band.width, out_row, len(sinks)
        )
        width = max(width, width_needed)
        height = max(height, max_row + 1)
        for i, (px, py) in enumerate(tiles):
            ports.append(
                PortCandidate(
                    id=f"{out_item}-out-{i}",
                    item=out_item,
                    direction="output",
                    side="east",
                    local_position=(px, py),
                    flow_entry_dir=EAST,
                    max_rate_per_sec=cap,
                )
            )

    return MacroCell(
        id=recipe,
        kind="recipe-band",
        width=width,
        height=height,
        entities=tuple(entities),
        ports=tuple(ports),
    )


def _input_connector(item: str, k: int, db: Database, belt: str, cap: float) -> MacroCell:
    """West-edge stub where an infinite input belt of ``item`` enters, fanned
    out into one east-edge port per consuming band."""
    entities: list[Entity] = [
        Entity(name=belt, position=Position(0.5, 0.5), direction=EAST),
    ]
    tiles, width_needed, max_row = _fanout_east(entities, belt, 1, 0, k)
    if k <= 1:
        # Give the stub some body so its port isn't on the same tile as the
        # entry belt.
        entities.append(Entity(name=belt, position=Position(1.5, 0.5), direction=EAST))
        tiles, width_needed = [(1, 0)], 2
    ports = tuple(
        PortCandidate(
            id=f"{item}-out-{i}",
            item=item,
            direction="output",
            side="east",
            local_position=(px, py),
            flow_entry_dir=EAST,
            max_rate_per_sec=cap,
        )
        for i, (px, py) in enumerate(tiles)
    )
    return MacroCell(
        id=f"in-{item}",
        kind="input-connector",
        width=width_needed,
        height=max_row + 1,
        entities=tuple(entities),
        ports=ports,
    )


def _output_collector(item: str, belt: str, cap: float) -> MacroCell:
    entities = tuple(
        Entity(name=belt, position=Position(x + 0.5, 0.5), direction=EAST) for x in range(2)
    )
    port = PortCandidate(
        id=f"{item}-in",
        item=item,
        direction="input",
        side="west",
        local_position=(0, 0),
        flow_entry_dir=EAST,
        max_rate_per_sec=cap,
    )
    return MacroCell(
        id="out",
        kind="output-collector",
        width=2,
        height=1,
        entities=entities,
        ports=(port,),
    )


def build_problem(
    plan: ProductionPlan,
    db: Database,
    belt: str = "transport-belt",
    inserter: str = "fast-inserter",
    long_inserter: str = "long-handed-inserter",
) -> MacroProblem:
    """Construct macros, nets, and pins for ``plan``."""
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    crafts = {ln.recipe: ln.crafts_per_sec for ln in plan.lines}
    cap = db.belts[belt].throughput

    # item -> recipes that consume it, in deterministic order.
    consumers: dict[str, list[str]] = {}
    for r in sorted(counts):
        for item in db.recipes[r].ingredients:
            consumers.setdefault(item, []).append(r)

    problem = MacroProblem(plan=plan)

    # Recipe bands. A band's product feeds its consuming bands and, for the
    # target item, the output collector.
    for r in sorted(counts):
        out_item = next(iter(db.recipes[r].products))
        sinks = list(consumers.get(out_item, []))
        if out_item == plan.target:
            sinks.append("out")
        macro = _band_macro(
            r, counts[r], sinks, db, belt, inserter, long_inserter, cap
        )
        problem.macros[macro.id] = macro
        for i, sink in enumerate(sinks):
            if sink == "out":
                rate = plan.rate
                sink_port = f"{out_item}-in"
            else:
                rate = crafts[sink] * db.recipes[sink].ingredients[out_item]
                sink_port = f"{out_item}-in"
            problem.nets.append(
                FlowNet(
                    id=f"{out_item}:{r}->{sink}",
                    item=out_item,
                    source_macro=r,
                    source_port=f"{out_item}-out-{i}",
                    sink_macro=sink,
                    sink_port=sink_port,
                    rate_per_sec=rate,
                )
            )

    # Raw-item input connectors on the west edge.
    raws = sorted(
        item for item in consumers if db.is_raw(item)
    )
    for item in raws:
        sinks = consumers[item]
        macro = _input_connector(item, len(sinks), db, belt, cap)
        problem.macros[macro.id] = macro
        problem.pins[macro.id] = "west"
        for i, sink in enumerate(sinks):
            rate = crafts[sink] * db.recipes[sink].ingredients[item]
            problem.nets.append(
                FlowNet(
                    id=f"{item}:in->{sink}",
                    item=item,
                    source_macro=macro.id,
                    source_port=f"{item}-out-{i}",
                    sink_macro=sink,
                    sink_port=f"{item}-in",
                    rate_per_sec=rate,
                )
            )

    # Target output collector on the east edge.
    collector = _output_collector(plan.target, belt, cap)
    problem.macros[collector.id] = collector
    problem.pins[collector.id] = "east"

    return problem
