"""CP-SAT placement for a single belt-based block (iteration 1).

We place every assembler (3x3) and every inserter (1x1) inside a fixed-width
bounding box and minimize the box height. Constraints:

* No two entity tiles overlap (CP-SAT ``add_no_overlap_2d``).
* Each inserter sits in the ring orthogonally adjacent to its parent machine,
  enforced as an allowed-assignment table over (dx, dy) offsets.

Each inserter exposes a *belt-side* tile one step beyond it (away from the
machine); these are the endpoints the routing stage will connect with belts.

Known limitations (deferred to later iterations):

* Belt-side tiles are not yet reserved/kept clear, and belts themselves are not
  placed here — that's the routing stage.
* Width is fixed per call (height is minimized); joint width/height search and
  multi-column "main-bus" templates come later.
* Inserter ``direction`` integers follow the convention documented below and
  should be verified once we can import into the game.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from factopt.data.database import Database
from factopt.evaluate import requirements
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Blueprint, Entity, Position
from factopt.ratios.solver import ProductionPlan

# (dx, dy) of the inserter tile relative to the machine's top-left, for a 3x3
# machine. These are the 12 ring tiles immediately around the footprint.
_RING_OFFSETS: list[tuple[int, int]] = (
    [(c, -1) for c in range(3)]  # top
    + [(c, 3) for c in range(3)]  # bottom
    + [(-1, r) for r in range(3)]  # left
    + [(3, r) for r in range(3)]  # right
)


@dataclass(frozen=True)
class PlacedEntity:
    """A placed assembler. ``x``/``y`` are the top-left tile coordinates."""

    name: str
    x: int
    y: int
    width: int
    height: int
    recipe: str | None = None

    def center(self) -> Position:
        return Position(self.x + self.width / 2.0, self.y + self.height / 2.0)


@dataclass(frozen=True)
class PlacedInserter:
    """A placed inserter and the tiles it bridges."""

    name: str
    x: int
    y: int
    direction: int
    item: str
    flow_dir: str  # "in" (belt->machine) or "out" (machine->belt)
    belt_x: int
    belt_y: int
    machine_index: int

    def center(self) -> Position:
        return Position(self.x + 0.5, self.y + 0.5)


@dataclass
class Placement:
    plan: ProductionPlan
    width: int
    height: int
    machines: list[PlacedEntity] = field(default_factory=list)
    inserters: list[PlacedInserter] = field(default_factory=list)
    status: str = ""

    @property
    def area(self) -> int:
        return self.width * self.height

    def belt_endpoints(self) -> list[tuple[int, int, str, str]]:
        """(x, y, item, flow_dir) belt-side tiles for the routing stage."""
        return [(i.belt_x, i.belt_y, i.item, i.flow_dir) for i in self.inserters]

    def to_blueprint(self, label: str | None = None) -> Blueprint:
        ents: list[Entity] = []
        for m in self.machines:
            ents.append(Entity(name=m.name, position=m.center(), recipe=m.recipe))
        for ins in self.inserters:
            ents.append(Entity(name=ins.name, position=ins.center(), direction=ins.direction))
        return Blueprint(label=label, entities=ents)


@dataclass
class _MachineInst:
    recipe: str
    name: str
    # One (item, flow_dir) per inserter this machine needs.
    inserters: list[tuple[str, str]]


def _machine_instances(plan: ProductionPlan, db: Database, inserter: str) -> list[_MachineInst]:
    ins_rate = db.inserters[inserter].rate
    speed = db.assemblers[plan.assembler].crafting_speed
    insts: list[_MachineInst] = []
    for line in plan.lines:
        recipe = db.recipes[line.recipe]
        pmc = speed / recipe.time
        specs: list[tuple[str, str]] = []
        for item, count in recipe.ingredients.items():
            per = math.ceil(count * pmc / ins_rate - 1e-9)
            specs += [(item, "in")] * per
        for item, count in recipe.products.items():
            per = math.ceil(count * pmc / ins_rate - 1e-9)
            specs += [(item, "out")] * per
        for _ in range(line.machines):
            insts.append(_MachineInst(recipe.name, plan.assembler, list(specs)))
    return insts


def _inserter_geometry(mx: int, my: int, ix: int, iy: int, flow_dir: str) -> tuple[int, int, int]:
    """Return (direction, belt_x, belt_y) for an inserter at (ix,iy) serving the
    machine whose top-left is (mx,my).

    Direction convention (Factorio blueprint quirk, verified in-game): an
    inserter's ``direction`` points toward the tile it PICKS UP from, which is
    the opposite of its in-game arrow / drop side. So an "in" inserter (belt ->
    machine) faces the belt, and an "out" inserter (machine -> belt) faces the
    machine. The belt-side tile is the cell one step away from the machine.
    """
    if ix < mx:  # left of machine; machine is to the East
        toward_machine, toward_belt, belt = EAST, WEST, (ix - 1, iy)
    elif ix >= mx + 3:  # right of machine; machine is to the West
        toward_machine, toward_belt, belt = WEST, EAST, (ix + 1, iy)
    elif iy < my:  # above machine; machine is to the South
        toward_machine, toward_belt, belt = SOUTH, NORTH, (ix, iy - 1)
    else:  # below machine; machine is to the North
        toward_machine, toward_belt, belt = NORTH, SOUTH, (ix, iy + 1)

    # Direction points at the pickup tile.
    direction = toward_belt if flow_dir == "in" else toward_machine
    return direction, belt[0], belt[1]


def place_block(
    plan: ProductionPlan,
    db: Database,
    width: int,
    inserter: str = "fast-inserter",
    max_height: int | None = None,
    time_limit_s: float = 10.0,
    workers: int = 8,
) -> Placement:
    """Place a block's machines and inserters in a width-``width`` box.

    Minimizes the bounding-box height. Raises if no feasible layout is found
    within ``time_limit_s``.
    """
    insts = _machine_instances(plan, db, inserter)
    n_machines = len(insts)
    n_inserters = sum(len(m.inserters) for m in insts)

    if width < 3:
        raise ValueError("width must be at least 3 (machine footprint)")

    total_cells = n_machines * 9 + n_inserters
    if max_height is None:
        # Generous bound: even a near-degenerate packing fits in this height.
        max_height = max(3, math.ceil(total_cells / width) * 3 + 6)

    model = cp_model.CpModel()
    H = model.new_int_var(3, max_height, "H")

    x_ivars, y_ivars = [], []  # intervals for no_overlap_2d
    m_x, m_y = [], []  # machine top-left vars

    for mi, _inst in enumerate(insts):
        x = model.new_int_var(0, width - 3, f"mx_{mi}")
        y = model.new_int_var(0, max_height - 3, f"my_{mi}")
        m_x.append(x)
        m_y.append(y)
        x_ivars.append(
            model.new_interval_var(x, 3, model.new_int_var(0, width, f"mxe_{mi}"), f"mix_{mi}")
        )
        y_ivars.append(
            model.new_interval_var(y, 3, model.new_int_var(0, max_height, f"mye_{mi}"), f"miy_{mi}")
        )
        model.add(y + 3 <= H)

    # Inserters, each tied to its machine via an allowed (dx,dy) offset table.
    ins_records: list[
        tuple[int, cp_model.IntVar, cp_model.IntVar, cp_model.IntVar, cp_model.IntVar, str, str]
    ] = []
    for mi, inst in enumerate(insts):
        for k, (item, flow_dir) in enumerate(inst.inserters):
            dx = model.new_int_var(-1, 3, f"dx_{mi}_{k}")
            dy = model.new_int_var(-1, 3, f"dy_{mi}_{k}")
            model.add_allowed_assignments([dx, dy], _RING_OFFSETS)
            ix = model.new_int_var(-1, width, f"ix_{mi}_{k}")
            iy = model.new_int_var(-1, max_height, f"iy_{mi}_{k}")
            model.add(ix == m_x[mi] + dx)
            model.add(iy == m_y[mi] + dy)
            # Keep inserter tiles inside the box.
            model.add(ix >= 0)
            model.add(ix <= width - 1)
            model.add(iy >= 0)
            model.add(iy + 1 <= H)
            x_ivars.append(
                model.new_interval_var(
                    ix, 1, model.new_int_var(0, width, f"ixe_{mi}_{k}"), f"iix_{mi}_{k}"
                )
            )
            y_ivars.append(
                model.new_interval_var(
                    iy, 1, model.new_int_var(0, max_height, f"iye_{mi}_{k}"), f"iiy_{mi}_{k}"
                )
            )
            ins_records.append((mi, ix, iy, dx, dy, item, flow_dir))

    model.add_no_overlap_2d(x_ivars, y_ivars)
    model.minimize(H)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    status = solver.solve(model)
    status_name = solver.status_name(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"placement infeasible/unsolved: {status_name}")

    placement = Placement(
        plan=plan,
        width=width,
        height=int(solver.value(H)),
        status=status_name,
    )
    for mi, inst in enumerate(insts):
        placement.machines.append(
            PlacedEntity(
                name=inst.name,
                x=int(solver.value(m_x[mi])),
                y=int(solver.value(m_y[mi])),
                width=3,
                height=3,
                recipe=inst.recipe,
            )
        )
    for mi, ix, iy, _dx, _dy, item, flow_dir in ins_records:
        ixv, iyv = int(solver.value(ix)), int(solver.value(iy))
        mxv, myv = placement.machines[mi].x, placement.machines[mi].y
        direction, bx, by = _inserter_geometry(mxv, myv, ixv, iyv, flow_dir)
        placement.inserters.append(
            PlacedInserter(
                name=inserter,
                x=ixv,
                y=iyv,
                direction=direction,
                item=item,
                flow_dir=flow_dir,
                belt_x=bx,
                belt_y=by,
                machine_index=mi,
            )
        )
    return placement
