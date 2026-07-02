"""Benders-style optimization loop (M5/M6).

Repeats master -> detailed routing -> cuts until a routable placement is
found (or the iteration budget runs out), then assembles and validates the
blueprint. The margin/area-slack schedule loosens the master when cuts alone
are not fixing infeasibility, mirroring the "minimize infeasibility first"
lexicographic intent.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from factopt.codec import encode
from factopt.data.database import Database
from factopt.macros import MacroProblem, build_problem
from factopt.master.cuts import BendersCut
from factopt.master.model import MasterSolution, solve_master
from factopt.model.blueprint import Blueprint
from factopt.ratios.solver import ProductionPlan, solve_ratios
from factopt.routing.explain import explain_failures
from factopt.routing.multinet import RoutingResult, route_nets
from factopt.validate import ValidationReport, validate

# (margin, area_slack) per iteration; repeats the last entry when exhausted.
_SCHEDULE = [(1, 0.0), (1, 0.15), (2, 0.15), (2, 0.3), (3, 0.3), (3, 0.5)]


@dataclass
class Iteration:
    index: int
    margin: int
    area_slack: float
    master: MasterSolution
    routing: RoutingResult | None
    new_cuts: list[BendersCut] = field(default_factory=list)


@dataclass
class Candidate:
    blueprint: Blueprint
    blueprint_string: str
    master: MasterSolution
    routing: RoutingResult
    validation: ValidationReport

    @property
    def width(self) -> int:
        return self.master.width

    @property
    def height(self) -> int:
        return self.master.height

    @property
    def area(self) -> int:
        return self.master.area


@dataclass
class LoopResult:
    problem: MacroProblem
    best: Candidate | None
    iterations: list[Iteration]
    cuts: list[BendersCut]

    @property
    def feasible(self) -> bool:
        return self.best is not None

    def summary(self) -> str:
        lines = []
        for it in self.iterations:
            status = "unsolved"
            if it.master.ok:
                if it.routing is not None and it.routing.feasible:
                    status = "routed"
                else:
                    kinds = (
                        [f.kind for f in it.routing.failures] if it.routing is not None else []
                    )
                    status = f"failed ({', '.join(kinds)})"
            lines.append(
                f"iter {it.index}: margin={it.margin} slack={it.area_slack:g} "
                f"bbox={it.master.width}x{it.master.height} {status}; "
                f"+{len(it.new_cuts)} cuts"
            )
        for cut in self.cuts:
            lines.append(f"  cut[{cut.kind}] {cut.explanation}")
        return "\n".join(lines)


def _assemble(
    problem: MacroProblem,
    master: MasterSolution,
    routing: RoutingResult,
    db: Database,
    label: str,
) -> Candidate:
    entities = list(routing.entities)
    for pm in master.placements.values():
        entities.extend(pm.entities())
    flows = [
        (
            master.port_tile(n.source_macro, n.source_port),
            master.port_tile(n.sink_macro, n.sink_port),
        )
        for n in problem.nets
    ]
    report = validate(entities, db, bounds=(0, 0, master.width, master.height), flows=flows)
    bp = Blueprint(label=label, entities=entities)
    return Candidate(
        blueprint=bp,
        blueprint_string=encode(bp),
        master=master,
        routing=routing,
        validation=report,
    )


def optimize_loop(
    target: str,
    rate: float,
    db: Database,
    plan: ProductionPlan | None = None,
    belt: str = "transport-belt",
    max_iterations: int = 8,
    coarse_cell: int | None = 4,
    master_time_limit_s: float = 20.0,
    time_budget_s: float = 240.0,
    label: str | None = None,
) -> LoopResult:
    """Run the Benders loop for ``rate`` items/s of ``target``."""
    if plan is None:
        plan = solve_ratios(target, rate, db)
    problem = build_problem(plan, db, belt=belt)
    label = label or f"{target}-benders-{rate:g}ps"

    cuts: list[BendersCut] = []
    iterations: list[Iteration] = []
    best: Candidate | None = None
    started = time.monotonic()

    for i in range(max_iterations):
        if time.monotonic() - started > time_budget_s:
            break
        margin, slack = _SCHEDULE[min(i, len(_SCHEDULE) - 1)]
        master = solve_master(
            problem,
            cuts=cuts,
            margin=margin,
            area_slack=slack,
            coarse_cell=coarse_cell,
            time_limit_s=master_time_limit_s,
        )
        it = Iteration(index=i, margin=margin, area_slack=slack, master=master, routing=None)
        iterations.append(it)
        if not master.ok:
            # All placements at this margin are cut off; the schedule will
            # loosen next round.
            continue

        routing = route_nets(problem, master, db, belt=belt)
        it.routing = routing
        if routing.feasible:
            best = _assemble(problem, master, routing, db, label)
            break

        new_cuts = explain_failures(problem, master, routing, db, belt=belt)
        it.new_cuts = new_cuts
        cuts.extend(new_cuts)

    return LoopResult(problem=problem, best=best, iterations=iterations, cuts=cuts)
