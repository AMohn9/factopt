# Factorio Blueprint Optimizer: Research-Backed Implementation Plan

## Goal

Build an optimizer that takes a production intent such as:

```yaml
target_item: logistic-science-pack
target_rate_per_minute: 60
allowed_external_inputs:
  - iron-plate
  - copper-plate
allowed_entities:
  - assembling-machine-1
  - transport-belt
  - underground-belt
  - splitter
  - inserter
objective:
  primary: feasible_and_meets_rate
  secondary: minimize_bounding_box_area
  tertiary: minimize_belts_undergrounds_and_total_entity_cost
```

and produces a valid Factorio blueprint that manufactures the target from infinite input resources.

The intended architecture is **not** a monolithic tile-level optimizer. The core design should be a staged optimizer that ties placement and routing together through a **logic-based Benders-style loop**:

```text
rate planning
  -> macro placement + coarse routing master problem
  -> detailed belt-routing subproblem / oracle
  -> routability cuts back to master
  -> blueprint emission + validation
```

The project should initially optimize a narrow but meaningful case, such as green/logistic science from infinite iron and copper plates, and then expand.

---

## Research summary

### 1. Factorio blueprint optimization is a real combinatorial optimization problem

Patterson et al., *Towards Automatic Design of Factorio Blueprints*, frame optimal blueprint design as a hard problem combining bin packing, routing, and network design. They explored constraint-programming models for blueprint generation and found that fully integrated models rapidly become difficult as layouts grow.

Reasoning for this project: this supports using decomposition rather than a single giant CP-SAT/MIP model over every tile, belt direction, inserter, and recipe.

Source: https://arxiv.org/html/2310.01505

### 2. Logic-based Benders decomposition is the right conceptual model

Classical Benders decomposition relies on LP dual cuts from a continuous subproblem. Our routing subproblem is combinatorial: grid paths, obstacles, belt directions, underground constraints, lane capacity, and inserter geometry. Hooker’s work on logic-based Benders decomposition generalizes Benders to cases where the subproblem can be any optimization problem and where cuts come from logical inference rather than only LP duals.

Reasoning for this project: use a master placement/coarse-routing model, solve detailed routing after placement is fixed, and feed back structured routing failures as cuts.

Source: https://arxiv.org/abs/1910.11944

### 3. The closest analogy is chip physical design

In VLSI placement/routing, cells have rectangular footprints, pins, obstacles, and nets. Placement is easy to make geometrically valid but hard to make routable. Routability-aware placers use coarse/global routing to estimate congestion before detailed routing. Brenner and Rohe describe routers working in two steps: coarse global routing estimates routability and guides a detailed/local router.

Reasoning for this project: model Factorio production macros as cells, belt/item flows as nets/commodities, inserter/belt access points as pins, and underground belts as a limited pseudo-third routing layer.

Source: https://www.cecs.uci.edu/~papers/compendium94-03/papers/2002/ispd02/pdffiles/01_1.pdf

### 4. CP-SAT is a good first solver for integer placement and discrete choices

Google OR-Tools CP-SAT is designed for integer programming problems and requires integer-valued constraints. Factorio layout decisions are naturally integer-valued: tile coordinates, orientations, macro choices, coarse-grid capacities, and discrete port choices.

Reasoning for this project: use CP-SAT for the master problem and for small local detailed-routing repairs. Avoid using CP-SAT as a monolithic whole-blueprint tile router at first.

Source: https://developers.google.com/optimization/cp/cp_solver

### 5. Blueprint input/output is tractable

Factorio blueprint strings are JSON compressed with zlib and base64-encoded with a version byte. As of Factorio 2.0, the game can also import uncompressed JSON blueprint strings directly. Draftsman is a Python library for importing, modifying, creating, and exporting Factorio blueprints.

Reasoning for this project: the optimizer can emit either blueprint JSON directly or use Draftsman as a higher-level adapter. Keep an internal representation independent of Draftsman so the solver is not coupled to blueprint serialization.

Sources:
- https://wiki.factorio.com/Blueprint_string_format
- https://factorio-draftsman.readthedocs.io/en/latest/

### 6. Game data should come from Factorio prototypes, not hand-coded tables

Wube publishes `factorio-data`, a repository tracking Lua prototype definitions between Factorio releases. This can provide recipe/entity definitions for vanilla data. For modded support, the long-term answer is likely consuming a prototype dump from the installed game/mod set.

Reasoning for this project: start with a small checked-in vanilla fixture for green science, but design the data layer to be driven by recipe/entity prototypes.

Source: https://github.com/wube/factorio-data

### 7. Belts require capacity and lane modeling

Factorio belts have two lanes. The Factorio wiki gives practical base-game throughput values: basic/yellow belts carry 15 items/s across both lanes; fast/red belts carry 30 items/s; express/blue belts carry 45 items/s. The physics page also emphasizes density, compression, and independent lanes.

Reasoning for this project: the first router can model whole-belt capacity, but the architecture should allow lane-level modeling later.

Source: https://wiki.factorio.com/Transport_belts/Physics

---

## Scope for the first serious prototype

### Include

- Vanilla base-game recipes only.
- One target item: `logistic-science-pack`.
- Infinite input belts entering from the west side of the blueprint.
- Output belt exiting from the east side of the blueprint.
- Assembling machines, inserters, transport belts, underground belts, splitters, and power poles.
- Recipe assignment and machine count calculation.
- Macro-level placement.
- Coarse routing in the master problem.
- Detailed belt routing as a subproblem.
- Static blueprint validation.

### Exclude initially

- Fluids.
- Trains.
- Logistic bots.
- Modules.
- Beacons.
- Quality.
- Space Age mechanics.
- Arbitrary mod support.
- Full lane balancing.
- Fully general belt braiding.
- Perfect global optimality claims.

These exclusions are deliberate. They keep the first milestone small enough to finish while preserving the main architectural challenge: placement and routing must inform each other.

---

## Core abstractions

### Item and recipe graph

```python
@dataclass(frozen=True)
class Item:
    name: str

@dataclass(frozen=True)
class Recipe:
    name: str
    category: str
    time_seconds: Fraction
    inputs: dict[Item, Fraction]
    outputs: dict[Item, Fraction]
```

The rate planner should turn the recipe graph into a production DAG or, later, a more general flow network with possible alternative recipes.

### Production node

```python
@dataclass(frozen=True)
class ProductionNode:
    id: str
    recipe: Recipe
    machine_name: str
    craft_rate_per_second: Fraction
    machine_count: int
```

### Flow edge

```python
@dataclass(frozen=True)
class FlowEdge:
    item: Item
    source_node_id: str | None   # None means external input
    sink_node_id: str | None     # None means final output
    rate_per_second: Fraction
```

### Macro cell

A macro is a reusable, routable layout block. The optimizer should not initially place every assembler, belt, and inserter from scratch. It should place macro cells with known footprints and ports.

```python
@dataclass(frozen=True)
class MacroCell:
    id: str
    kind: str
    width: int
    height: int
    blocked_tiles: frozenset[tuple[int, int]]
    entities_template: tuple[EntityTemplate, ...]
    ports: tuple[PortCandidate, ...]
    internal_capacity: dict[str, Fraction]
```

Examples:

- `single_assembler_two_input_one_output`
- `assembler_row_input_west_output_east`
- `gear_block`
- `circuit_block`
- `green_science_block`
- `input_bus_connector`
- `output_collector`

### Port candidate

```python
@dataclass(frozen=True)
class PortCandidate:
    id: str
    item: str
    direction: Literal["input", "output"]
    side: Literal["north", "south", "east", "west"]
    local_position: tuple[int, int]
    lane: int | None
    max_rate_per_second: Fraction
```

Ports are where placement and routing meet. Good port modeling is critical.

### Coarse grid

The master problem should reason over a coarse grid, for example 4x4 or 8x8 tile bins.

```python
@dataclass(frozen=True)
class CoarseCell:
    i: int
    j: int
    tile_bounds: Rect

@dataclass(frozen=True)
class CoarseArc:
    source: tuple[int, int]
    target: tuple[int, int]
    orientation: Literal["horizontal", "vertical"]
    estimated_lane_capacity: int
```

This allows the master to estimate routing pressure without committing to exact belt tiles.

### Cut

All feedback from the detailed router should be serializable and inspectable.

```python
@dataclass(frozen=True)
class BendersCut:
    kind: Literal[
        "corridor_capacity",
        "pin_access",
        "escape_capacity",
        "relative_ordering",
        "underground_feasibility",
        "nogood",
        "congestion_price",
    ]
    affected_macros: tuple[str, ...]
    affected_flows: tuple[str, ...]
    payload: dict[str, Any]
    explanation: str
```

---

## Level 0: rate planning

The first planner can be deterministic and simple.

Variables:

```text
x_r = crafts per second of recipe r
m_r = integer machine count for recipe r
```

Item balance:

```text
external_input_i + sum_r output_rate(r, i) >= target_i + sum_r input_rate(r, i)
```

Machine count:

```text
m_r >= x_r / effective_crafts_per_second(machine, recipe)
```

Initial simplification:

1. Use hand-selected recipes for green science.
2. Compute fractional rates exactly using `fractions.Fraction`.
3. Round machine counts up.
4. Produce a flow graph between production blocks.

Later improvements:

- Alternative recipes.
- Integer optimization over recipe choices.
- Module and beacon effects.
- Multi-target outputs.
- Reuse of intermediate products from allowed external inputs.

---

## Level 1: master problem — macro placement plus coarse routing

The master should include both placement and a coarse routability model. A pure placement master would learn too slowly because it would repeatedly propose compact but unroutable layouts.

### Decision variables

For each macro `m`:

```text
x_m, y_m              integer tile position
o_m                   orientation
w_m, h_m              orientation-dependent dimensions
```

For each macro pair:

```text
left_of[m,n], above[m,n]   Boolean disjunctive no-overlap helpers
```

For each flow `e` and coarse arc `a`:

```text
f[e,a] = integer or scaled-integer flow units assigned to coarse arc a
```

For each coarse arc `a`:

```text
used_capacity[a]
slack_capacity[a]
```

### Constraints

#### Non-overlap

For every pair of macros `m, n`, enforce at least one of:

```text
m is left of n
n is left of m
m is above n
n is above m
```

#### Bounding box

```text
0 <= x_m
0 <= y_m
x_m + w_m <= bbox_width
y_m + h_m <= bbox_height
```

#### Flow conservation on coarse grid

For each item flow `e`, route from the coarse cell containing its source port to the coarse cell containing its sink port:

```text
sum_out(f[e,*], source_cell) - sum_in(f[e,*], source_cell) = demand_e
sum_in(f[e,*], sink_cell) - sum_out(f[e,*], sink_cell) = demand_e
intermediate cells: sum_in = sum_out
```

Use scaled integer flow units, e.g. one unit equals 1 item/s or 1/4 item/s.

#### Coarse capacity

```text
sum_e f[e,a] <= estimated_capacity[a]
```

Capacity should depend on how much free space exists in the associated coarse boundary. If a macro blocks most of a coarse boundary, that boundary should have lower capacity.

#### Port access preconditions

For each chosen port, require at least one access pattern to be potentially open. Do not wait for detailed routing to discover all boxed-in ports.

### Objective

Use a lexicographic objective, implemented either through sequential solves or large weights:

1. Minimize infeasibility/slack.
2. Minimize bounding-box area.
3. Minimize bounding-box perimeter.
4. Minimize estimated belt length.
5. Minimize coarse congestion.
6. Minimize entity/build cost.
7. Minimize ugliness penalties such as excessive detours or isolated pockets.

A single scalar is okay internally, but externally report the decomposed score.

---

## Level 2: detailed routing subproblem

Given fixed macro placements, orientations, port choices, and coarse route guidance, the detailed router tries to instantiate exact belts, undergrounds, splitters, and inserter-access belts.

### Inputs

```python
@dataclass(frozen=True)
class RoutingProblem:
    placed_macros: tuple[PlacedMacro, ...]
    flows: tuple[FlowEdge, ...]
    coarse_routes: dict[str, tuple[CoarseArc, ...]]
    allowed_entities: AllowedEntities
    belt_tier: str
    grid_bounds: Rect
```

### Outputs

```python
@dataclass(frozen=True)
class RoutingResult:
    feasible: bool
    route_entities: tuple[Entity, ...]
    flow_paths: dict[str, FlowPath]
    failures: tuple[RoutingFailure, ...]
    metrics: RoutingMetrics
```

### Initial routing algorithm

Use a layered approach:

1. Build a grid graph of available tiles.
2. Mark macro footprints and reserved access tiles as obstacles.
3. Order flows by difficulty: high rate first, shortest slack first, fewest available ports first.
4. Route each flow using A* with costs for distance, turns, congestion, and coarse-route deviation.
5. Use rip-up-and-reroute when later flows fail.
6. If a small region remains unresolved, formulate that region as CP-SAT.

### Why not start with full exact routing?

A full exact tile model across the whole blueprint will likely be too slow and hard to debug. The detailed router should be heuristic globally and exact locally.

---

## Benders-style feedback loop

The main optimization loop:

```python
cuts: list[BendersCut] = []
incumbents: list[BlueprintCandidate] = []

while not time_budget.expired():
    master_solution = solve_master(rate_plan, macro_library, cuts)

    if master_solution.status not in {"FEASIBLE", "OPTIMAL"}:
        break

    routing_result = solve_detailed_routing(master_solution)

    if routing_result.feasible:
        candidate = emit_and_validate_blueprint(master_solution, routing_result)
        incumbents.append(candidate)
        cuts.extend(make_congestion_price_cuts(routing_result))
    else:
        cuts.extend(explain_routing_failures(master_solution, routing_result))

return best_candidate(incumbents)
```

This is Benders-like because:

- The master controls high-level placement and coarse routing.
- The subproblem checks detailed routability.
- The subproblem returns constraints that rule out or penalize bad master choices.

It is logic-based rather than classical Benders because cuts come from routing explanations, min-cuts, pin-access reasoning, or no-good patterns rather than LP duals.

---

## Cut families

### 1. Corridor capacity cuts

Failure pattern: a narrow corridor separates producers from consumers, and the required item flow exceeds the number of belt lanes that can physically cross the corridor.

Detection:

- Build a graph of free tiles or coarse cells.
- Compute a min-cut between source-side and sink-side regions for one or more commodities.
- Compare required lanes to available crossing capacity.

Cut idea:

```text
required_lanes_crossing_separator <= available_lanes_on_separator
```

Master response:

- Increase spacing.
- Move producers and consumers to reduce crossing demand.
- Route some flow through another coarse channel.
- Change macro orientation or port choice.

This should be the first serious cut family implemented.

### 2. Pin-access cuts

Failure pattern: a macro has a valid rectangle placement, but its input/output port is boxed in by neighboring macros or reserved belts.

Cut idea:

```text
For port group p:
  at least one candidate access tile must remain unblocked
```

This can be enforced preemptively in the master for known macro port candidates.

### 3. Escape-capacity cuts

Failure pattern: a port is locally accessible, but there is not enough boundary capacity for required belts to escape the neighborhood around a macro.

Detection:

- Draw a small box around the macro.
- Count required incoming/outgoing belt lanes.
- Count free boundary exits.

Cut idea:

```text
required_lanes_entering_or_leaving_box <= available_boundary_exits
```

This is stronger than simply leaving one tile of padding around each assembler.

### 4. Relative-ordering cuts

Failure pattern: flows become impossible or expensive because macro ordering forces crossings in a narrow region.

Cut idea:

```text
not (A north of B and C south of D and all flows must cross in corridor K)
```

Use this sparingly. Prefer capacity cuts when possible, because relative-ordering cuts can overfit to one failed placement.

### 5. Underground-feasibility cuts

Failure pattern: the coarse route assumes a crossing can be solved by underground belts, but the exact distance, direction, or entry/exit tiles do not work.

Cut idea:

```text
If corridor C requires k crossings, reserve k compatible straight underground crossing slots.
```

Initially, avoid sophisticated belt braiding. Add this family once the basic router works.

### 6. No-good cuts

Failure pattern: the router cannot produce a useful explanation yet.

Cut idea:

```text
forbid this exact combination of macro coarse positions and orientations
```

No-good cuts are useful as a fallback, but they are weak. The router should eventually return structured explanations.

### 7. Congestion-price cuts

Failure pattern: routing succeeds but is ugly, long, or nearly saturated.

Cut idea:

- Increase the cost of using congested coarse arcs.
- Penalize macro placements that recreate the same bottleneck.
- Penalize route patterns that require many underground belts or excessive turns.

This is not a hard feasibility cut. It is closer to negotiated congestion in chip routing.

---

## Validation

### Static validation

Before importing into Factorio, verify:

- No entity overlap.
- All entities are within blueprint bounds.
- Every assembler has the intended recipe.
- Every inserter has a valid pickup and dropoff target.
- Every belt path is directionally connected.
- Every required flow has a path from source to sink.
- Throughput estimates do not exceed modeled belt/inserter capacities.
- Power poles cover all powered entities, if power is included in scope.

### Dynamic validation

Eventually, run a headless Factorio scenario or validation mod that:

- Places the generated blueprint.
- Supplies infinite inputs.
- Runs for a fixed number of ticks.
- Measures output rate.
- Reports bottleneck locations.

Do not rely only on static throughput formulas forever. Inserter and lane behavior will eventually matter.

---

## Metrics

Report every candidate with decomposed metrics:

```yaml
feasible: true
meets_rate: true
target_rate_per_minute: 60
estimated_rate_per_minute: 62.5
bounding_box:
  width: 42
  height: 18
  area: 756
entities:
  assembling_machines: 12
  inserters: 34
  belts: 218
  underground_belts: 18
  splitters: 2
routing:
  total_belt_length: 218
  total_turns: 47
  max_coarse_congestion: 0.83
  failed_routes: 0
score_breakdown:
  area_score: 756
  entity_cost_score: 1234
  congestion_score: 37
```

This makes optimizer behavior debuggable and avoids hiding everything behind one opaque score.

---

## Proposed repository structure

```text
factorio-blueprint-optimizer/
  README.md
  pyproject.toml
  docs/
    factorio_blueprint_optimizer_plan.md
    modeling_notes.md
    cut_families.md
  src/fbo/
    data/
      prototypes.py
      vanilla_fixture.py
    rate/
      planner.py
      graph.py
    macros/
      library.py
      templates.py
      ports.py
    master/
      model.py
      solve.py
      coarse_grid.py
      cuts.py
    routing/
      grid.py
      astar.py
      ripup.py
      local_cpsat.py
      explain.py
    blueprint/
      entities.py
      emit_json.py
      draftsman_adapter.py
      validate_static.py
    eval/
      metrics.py
      visualize.py
  tests/
    test_rate_green_science.py
    test_macro_ports.py
    test_master_no_overlap.py
    test_coarse_capacity_cut.py
    test_router_simple_paths.py
    test_blueprint_roundtrip.py
```

---

## Milestone plan

### Milestone 0: scaffold and data fixtures

Deliverables:

- Python package skeleton.
- Basic data classes.
- Hand-coded vanilla fixture for the green-science dependency chain.
- Basic blueprint JSON emitter.
- Unit tests for blueprint round-trip structure.

Acceptance criteria:

- Can emit a minimal blueprint JSON with one assembler and one belt.
- Can optionally convert it into a blueprint string or hand it to Draftsman.

### Milestone 1: rate planner

Deliverables:

- Compute recipe rates and machine counts for green science.
- Produce a production graph and item-flow graph.

Acceptance criteria:

- Given `60 logistic-science-pack/min`, output required rates for belts, inserters, gears, circuits, cable, etc.
- All item balances close exactly under rational arithmetic.

### Milestone 2: macro library

Deliverables:

- A small library of hand-authored macro cells.
- Ports for each macro.
- Internal templates for assemblers, inserters, and local belts.

Acceptance criteria:

- Can instantiate macro cells at arbitrary positions and orientations.
- Can emit their internal entities into blueprint JSON.
- Static validator catches overlap and invalid port access.

### Milestone 3: master placement without detailed routing

Deliverables:

- CP-SAT model for macro placement.
- No-overlap constraints.
- Bounding-box objective.
- Weighted Manhattan flow-distance objective.

Acceptance criteria:

- Can place all green-science macros without overlap.
- Can produce multiple feasible placements with different area/flow-distance tradeoffs.

### Milestone 4: coarse routing in the master

Deliverables:

- Coarse grid construction.
- Coarse flow variables.
- Coarse arc capacity estimates.
- Congestion-aware objective.

Acceptance criteria:

- Master avoids obvious chokepoints that a distance-only placement would create.
- Debug visualization shows macros, coarse cells, coarse routes, and saturated arcs.

### Milestone 5: detailed router

Deliverables:

- Tile grid builder.
- A* router for belt paths.
- Obstacle handling.
- Basic underground belt support.
- Rip-up-and-reroute loop.

Acceptance criteria:

- Can route simple one-item flows around placed macros.
- Can route the green-science production graph for at least one hand-friendly placement.
- Returns structured failure objects when routing fails.

### Milestone 6: Benders-style cut loop

Deliverables:

- `RoutingFailure -> BendersCut` conversion.
- Corridor capacity cuts.
- Pin-access cuts.
- Escape-capacity cuts.
- Fallback no-good cuts.

Acceptance criteria:

- Construct a test case where the first placement is unroutable.
- Router explains the failure.
- Master adds a cut.
- Next placement avoids the same failure.

### Milestone 7: blueprint validation and scoring

Deliverables:

- Full static validator.
- Candidate scoring.
- SVG/PNG/debug-grid visualization.
- Markdown report per generated candidate.

Acceptance criteria:

- A complete generated green-science blueprint can be inspected, scored, and imported into Factorio.

### Milestone 8: expansion

Potential next features:

- Multiple belt tiers.
- Lane-level routing.
- Splitter-aware distribution.
- Inserter throughput modeling.
- Power pole placement.
- Modules and beacons.
- Fluids.
- Full prototype loading from Factorio data.
- Headless Factorio dynamic validation.

---

## Important implementation guidance for Codex

1. Keep solver-independent data models pure and serializable.
2. Do not mix blueprint serialization with optimization logic.
3. Every solver output should have a debug visualization path.
4. Every routing failure should be explainable, even if the first explanation is only a weak no-good cut.
5. Prefer exactness in small local subproblems and heuristics at the whole-blueprint scale.
6. Make all units explicit: items/s, crafts/s, tiles, lanes, belt capacity units.
7. Use rational arithmetic in the rate planner; use scaled integers in CP-SAT.
8. Keep macro templates simple and boring at first. The optimizer should prove the architecture before trying to rediscover expert Factorio patterns.
9. Do not claim optimality unless the relevant solver actually proved it for the scoped model.
10. Log every cut added to the master with a human-readable explanation.

---

## First end-to-end demo target

Input:

```yaml
target_item: logistic-science-pack
target_rate_per_minute: 60
external_inputs:
  iron-plate: infinite westbound input belt
  copper-plate: infinite westbound input belt
allowed_entities:
  assembling-machine-1
  inserter
  transport-belt
  underground-belt
  splitter
objective_order:
  - feasible
  - meets_target_rate
  - minimize_area
  - minimize_total_belt_length
  - minimize_underground_count
```

Output:

- `candidate.blueprint.json`
- `candidate.blueprint.txt`
- `candidate_report.md`
- `candidate_debug.svg`

The report should include:

- Rate plan.
- Macro placement.
- Coarse routing utilization.
- Detailed route metrics.
- Cuts used during optimization.
- Static validation results.

---

## Open research questions

1. How much of routing should be modeled in the master before solve time becomes too slow?
2. Are corridor min-cut cuts strong enough to avoid most unroutable placements?
3. What is the right coarse-cell size: 4x4, 6x6, 8x8, or adaptive?
4. How should mixed belts and lane assignment be represented without exploding the search space?
5. When should underground belts be modeled as routing capacity versus detailed routing repair?
6. Can macro libraries be generated automatically from smaller verified cells?
7. Can router failures be clustered into reusable cut templates?
8. How much simulation is needed before static validation becomes trustworthy?

---

## References

- Patterson, Espasa, Chang, Hoffmann, *Towards Automatic Design of Factorio Blueprints*: https://arxiv.org/html/2310.01505
- Hooker, *Logic-based Benders decomposition for large-scale optimization*: https://arxiv.org/abs/1910.11944
- Brenner and Rohe, *An Effective Congestion Driven Placement Framework*: https://www.cecs.uci.edu/~papers/compendium94-03/papers/2002/ispd02/pdffiles/01_1.pdf
- Google OR-Tools CP-SAT documentation: https://developers.google.com/optimization/cp/cp_solver
- Factorio blueprint string format: https://wiki.factorio.com/Blueprint_string_format
- Factorio Draftsman documentation: https://factorio-draftsman.readthedocs.io/en/latest/
- Wube Factorio data repository: https://github.com/wube/factorio-data
- Factorio transport belt physics: https://wiki.factorio.com/Transport_belts/Physics
- Reid et al., *The Factory Must Grow: Automation in Factorio*: https://arxiv.org/abs/2102.04871
- Venturini, *Learning Solver Design: Automating Factorio Balancers*: https://gianlucaventurini.com/posts/2024/factorio-sat
