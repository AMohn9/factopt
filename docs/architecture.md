# Code architecture

This document maps the codebase: what each module does, what data flows
between them, and where the boundaries are. The optimization formulation
itself — the master model, coarse routing, cuts, and loop dynamics — is
covered in depth in [optimization-model.md](optimization-model.md); this page
stays at the "what lives where and why" level.

## The pipeline at a glance

```text
                 factopt.optimize.optimize(item, rate)          ← entrypoint
                        │  runs both flavours, keeps tightest block
                        ▼
                 factopt.loop.optimize_loop                     ← the Benders loop
   ┌────────────────────┼──────────────────────────────┐
   │                    │                              │
   ▼                    ▼                              ▼
factopt.ratios     factopt.macros                factopt.master
solve_ratios  ──▶  build_problem  ──────────▶    solve_master
(LP: machine       (MacroProblem: cells,         (CP-SAT: placement +
 counts, flows)     ports, trunk nets, pins)      coarse routing + cuts)
                        │                              │ MasterSolution
                        │                              ▼
                        │                    factopt.routing.multinet
                        │                    route_nets  (belt trees)
                        │                       │ ok?          │ failed
                        │                       ▼              ▼
                        │              factopt.validate   factopt.routing.explain
                        │              (static checks)    + factopt.master.cuts
                        │                       │              │ BendersCuts
                        │                       ▼              └──▶ next master solve
                        └──────────────▶  factopt.codec.encode
                                          (blueprint string)
```

Supporting layers, used throughout: `factopt.model` (entity/blueprint DTOs),
`factopt.data` (game data), `factopt.report` (SVG + markdown artifacts),
`factopt.sim` (headless-Factorio measurement).

## Module reference

### Data and I/O foundation

- **`factopt.model`** — solver-facing DTOs, no game logic.
  `model.blueprint` defines `Entity`, `Position`, `Blueprint` and the
  direction constants (Factorio 2.0's 16-way enum: `NORTH=0`, `EAST=4`, …).
  Coordinates are integer tiles, `y` grows downward, entity positions are tile
  centers. `model.game` defines the prototype dataclasses (`Recipe`,
  `Assembler`, `Belt`, `Inserter`).
- **`factopt.data`** — `database.Database` bundles recipes and prototypes for
  one ruleset and defines rawness (an item with no producing recipe is a
  freely supplied input); `Database.with_inputs(items)` returns a copy that
  additionally treats named intermediates as raw, which is how a caller feeds
  pre-built inputs (e.g. circuits) into a block instead of synthesizing them.
  `data.factorio` normalizes recipes from Draftsman's
  bundled vanilla 2.0 prototypes; `data.vanilla` adds curated inserter
  throughputs and the explicit raw-item boundary, and exposes the ready-to-use
  `vanilla.DB`.
- **`factopt.codec`** — blueprint-string encode/decode via Draftsman.
  Encoding constructs real Draftsman entities, which buys prototype validation
  and collision checking for free; decoding parses the raw JSON directly.

### Stage modules (in pipeline order)

- **`factopt.ratios.solver`** — the ratio LP (PuLP/CBC). Walks the recipe tree
  from the target, solves flow balance for crafts/s per recipe, returns a
  `ProductionPlan` (machine counts per recipe + aggregate `ItemFlow`s). Runs
  once per optimization, outside the loop.
- **`factopt.band`** — the single-recipe **band** primitive: one machine row
  with up to four horizontal belt lanes (near/far × above/below) reached by
  normal and long-handed inserters, items assigned to lanes by a small
  load-balancing heuristic. Bands are the building block that
  `factopt.macros` wraps into placeable cells.
- **`factopt.placement.dense`** — the boundary-aware **direct-insertion**
  placer: a fusable producer/consumer recipe pair laid out as one horizontal
  machine row, the intermediate item passed machine-to-machine through
  inserter gap columns (never belted), raws and product on straight full-width
  edge lanes. Contains its own small CP-SAT model (`_order_row`) to order
  producers/consumers so every consumer is exactly fed by adjacent neighbours.
  `plan_fusions` picks which recipe pairs fuse (single-producer,
  single-consumer internal items, validated by test-packing).
  `factopt.placement.ordering` is a general 1-D recipe-ordering utility
  (flow-weighted linear arrangement; brute force ≤ 8 recipes, CP-SAT beyond).
- **`factopt.macros`** — the placement abstraction layer.
  - `macros.cell` defines `MacroCell` (rectangular footprint, pre-baked
    entities, `PortCandidate`s), `rotated` (quarter-turn variants with
    entities/ports/directions rotating in lockstep), reversible-lane support
    (`PortEnd`, `ReversibleLane`), and `PlacedMacro` (a cell at a position +
    orientation + per-port reversal choice, able to emit its global-coordinate
    entities). `PlacedMacro.port_through_exit` reports where a belt fed into a
    full-span reversible lane re-emerges on the far edge — the geometry the
    router needs to run one belt *through* a consumer instead of splitting to
    it.
  - `macros.library` builds the `MacroProblem` for a plan: band and dense
    cells, west-pinned raw-input connectors, the east-pinned output collector,
    the trunk partition (consumers packed into belt-capacity bins), and one
    multi-sink `FlowNet` per trunk.
- **`factopt.master`** — the CP-SAT master problem.
  - `master.model` — placement variables/constraints, port-position
    expressions, the two-stage lexicographic solve (`solve_master`), and
    `MasterSolution`.
  - `master.coarse` — the binned Steiner-flow routing extension with
    placement-dependent capacities and the congestion objective terms.
  - `master.cuts` — `BendersCut` (serializable, self-explaining) and
    `apply_cuts`, which compiles accumulated cuts into a fresh model.
  - `master.backend` — the solver facade (`base` defines the op set;
    `cpsat` and `scip` implement it). Model-building code is
    solver-agnostic; SCIP linearizes CP-SAT's globals with big-M.
- **`factopt.routing`** — the detailed-routing oracle.
  - `routing.astar` — direction-aware single-path A\* over (tile, heading)
    states with underground-belt support; the shared search core. Besides
    surface and underground moves it supports optional **lane edges**: a
    caller-supplied "feed this consumer's lane and jump to its far side" move,
    which is how a belt is routed *through* a consumer.
  - `routing.steiner` — `route_tree`: grows one net's belt tree (trunk to the
    farthest sink, then Prim-style branches). Each sink is served either by a
    **splitter junction** seeded on a straight tree belt or, when its consumer
    has a through-lane (`sink_exits`), by a **pass-through** run that continues
    from the lane's far edge — A\* picks the cheaper (`through_cost` vs
    `splitter_cost`) per sink, yielding a hybrid splitter/pass-by tree.
  - `routing.multinet` — `route_nets`: negotiated congestion across all nets
    (present + history costs, whole-tree rip-up, hardening and targeted-rip-up
    fallbacks), endpoint reservation and pre-checks, structured
    `RoutingFailure`s. Reads each placed sink's `port_through_exit` and passes
    the per-sink exit tiles into `route_tree`.
  - `routing.explain` — failure attribution: floods the region reachable from
    a failed net's start to find the walling macros, and emits the
    corresponding cuts.
- **`factopt.validate`** — static validator run on every candidate before it
  becomes the incumbent: tile overlap, bounds, inserter pickup/dropoff, belt
  chaining, and directed source→sink belt-path checks (splitter- and
  underground-aware). Returns `Violation`s; callers decide severity.
- **`factopt.loop`** — `optimize_loop`: the Benders loop orchestrator. Owns
  the margin/area-slack schedule, the incumbent and its strict-area bound, the
  time budget, and per-iteration bookkeeping (`Iteration`, `LoopResult` with a
  human-readable `summary()`).
- **`factopt.optimize`** — `optimize`: the top-level selector. Runs the loop
  as `benders` (belt-only) and `dense` (`fuse=True`), keeps the tightest
  complete, validated, target-meeting candidate (`OptimizedBlock`).
- **`factopt.report`** — `render_svg` (macro rectangles, ports, nets, coarse
  grid utilization, detailed routes) and `write_candidate`, which drops
  `.blueprint.txt` / `.report.md` / `.debug.svg` artifacts for a loop run.
- **`factopt.sim`** — headless-Factorio measurement harness: builds a
  blueprint in a scenario, feeds raws from infinity chests, runs fast, and
  reads real items/s from the force's flow statistics. Import-safe and
  unit-testable without Factorio; only `run_headless` shells out.

### Scripts and artifacts

- `scripts/steiner_run.py` — CLI over `optimize_loop` + `write_candidate`
  (sweeps master time limit / iteration count, selects backend).
- `scripts/backend_bench.py` — CP-SAT vs SCIP master benchmark.
- `blueprints/` — checked-in sample outputs (`best/`, `benders/`, `dense/`),
  each with its blueprint string and, for loop runs, report + debug SVG.
- `tests/` — unit and end-to-end tests per module (`pytest`).

## Key data types (the pipeline's interfaces)

| Type | Module | Produced by | Consumed by |
|------|--------|-------------|-------------|
| `ProductionPlan` | `ratios.solver` | `solve_ratios` | `build_problem`, dense placer |
| `MacroProblem` (cells, `FlowNet`s, pins) | `macros.library` | `build_problem` | master, router, report |
| `MasterSolution` (`PlacedMacro`s, bbox, coarse routes) | `master.model` | `solve_master` | router, cuts, assembly |
| `RoutingResult` (entities, paths, `RoutingFailure`s) | `routing.multinet` | `route_nets` | loop, `explain_failures` |
| `BendersCut` | `master.cuts` | `explain_failures` | next `solve_master` |
| `Candidate` / `LoopResult` | `loop` | `optimize_loop` | `optimize`, report |
| `Blueprint` / blueprint string | `model` / `codec` | assembly + `encode` | user, sim |

Two conventions hold everywhere and are worth internalizing:

- **Geometry**: integer tile coordinates, origin top-left, `y` grows south;
  entity positions are tile centers (`x + 0.5`); directions use Factorio
  2.0's 16-way enum in steps of 4.
- **Cells own their interior; the router owns the space between.** Everything
  inside a `MacroCell` footprint is pre-validated at authoring time; the
  master only sees rectangles + ports, and the router only ever places belts
  on free tiles outside footprints. The single point of contact is the port
  access tile, one step outside the footprint.
