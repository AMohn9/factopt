# factopt — a Factorio blueprint optimizer

Given a production goal (an item and a rate), factopt synthesizes a compact,
**belt-based** production block and emits it as an importable **vanilla Factorio
2.0** blueprint string.

## Approach

The problem is decomposed like an EDA physical-design flow — ratios → placement →
routing → evaluation — and the pipeline is fronted by a selector that runs
several placement strategies and keeps the best complete block.

The general-purpose core is a **logic-based Benders-style loop**
(`factopt.loop`): a CP-SAT master places macro cells (recipe bands with
explicit ports) and routes coarse per-net flows over a capacity-aware cell
grid; a negotiated-congestion multi-net router then instantiates exact belts;
routing failures come back as structured cuts (no-good, pin-access, corridor)
that constrain the next master solve.

Documentation:

- [docs/optimization-model.md](docs/optimization-model.md) — the full
  optimization writeup: decomposition rationale, master formulation
  (placement, orientation, coarse Steiner flows, lexicographic objective),
  the routing oracle, cut families, and loop dynamics.
- [docs/architecture.md](docs/architecture.md) — module-by-module code
  structure and the data types flowing between stages.
- [`factorio_blueprint_optimizer_plan.md`](factorio_blueprint_optimizer_plan.md)
  — the original research survey and design plan.

| Stage | Module | Method |
|-------|--------|--------|
| Ratios / recipe selection | `factopt.ratios` | Linear programming (PuLP/CBC) |
| Macro cells + ports | `factopt.macros` | Band/dense cells, one multi-sink net per belt trunk |
| Master placement + coarse routing | `factopt.master` | CP-SAT (no-overlap, Steiner coarse flows, cuts); pluggable solver backend (SCIP experimental) |
| Detailed routing | `factopt.routing` | Multi-net negotiated congestion over Steiner-tree A\* (splitter junctions) |
| Cut loop | `factopt.loop` | master → route → explain failures → cuts |
| Static validation | `factopt.validate` | Overlap, bounds, inserters, belt-path flows |
| Selection | `factopt.optimize` | Run the loop (belt + dense fusion), keep tightest complete block |
| Reporting | `factopt.report` | SVG debug rendering + markdown candidate report |
| Ground truth | `factopt.sim` | Headless Factorio measurement |

I/O and game data are handled by:

- `factopt.model` — lightweight, solver-facing entity/blueprint DTO (directions
  in Factorio's 2.0 16-way enum).
- `factopt.codec` — blueprint-string encode/decode via
  [Draftsman](https://github.com/redruin1/factorio-draftsman). Encoding builds
  real Draftsman entities (validation + collision for free); decoding parses the
  raw JSON directly.
- `factopt.data` — recipe + entity data loaded from Draftsman's bundled Factorio
  2.0 prototypes (`factopt.data.factorio` normalizes recipes; curated inserter
  throughputs and an explicit raw-item boundary live in `factopt.data.vanilla`).

---

## Status

**Working end-to-end.** `optimize(item, rate)` returns an importable block for
every recipe tried so far (green circuits, red science, green science) via the
single general-purpose Benders loop (`factopt.loop`), which places, routes,
validates, and reports candidates with zero layout assumptions. The `dense`
flavour packs a fusable chain as a **direct-insertion** cell inside that same
loop, and items feed multiple consumers via **Steiner-tree routing**: one net
per belt trunk with all its sinks, grown as a real belt tree with splitters
dropped at the junctions (the VLSI-style answer, replacing the earlier
pass-through chaining). **Input belt lanes are reversible** — since machines
only *pick* from an input lane, the master feeds each from whichever end
(west/east, or north/south once rotated) shortens the route, decided as a
per-lane variable alongside the quarter-turn orientation.

The earlier hand-rolled generators (`compact`/`mvp`, `bus`, `line`) and the
interior-only research placers (`placement.flow`/`belt`/`cpsat`/`direct`) have
been retired now that the loop is the standard place-and-route path.

### Foundations (done)

- [x] **Game data via Draftsman**, pinned to vanilla 2.0. Full fluid-free recipe
  set (not a hand-maintained subset).
- [x] **Blueprint codec** via Draftsman (round-trips; emits valid 2.0 strings).
- [x] **Ratio LP solver** — machine counts + per-item flows for a goal.
- [x] **A\* belt router** — single-commodity, underground-belt aware.
- [x] **Steiner-tree router** (`routing.steiner`) — multi-sink nets: the trunk
  routes to the first sink, every later sink routes *to any tile of the
  existing tree* via multi-source A\* seeded with one candidate **splitter
  junction** per straight tree belt (2-tile, direction-constrained geometry).

### Placement strategy (done)

The single place-and-route path is the general-purpose cut loop, in two
flavours (`benders` = belt-only, `dense` = with direct-insertion fusion). Both
are thin wrappers over `loop.optimize_loop`; `optimize()` runs both and keeps
the tightest complete block.

- [x] `loop.optimize_loop` (`benders`) — the **general-purpose cut loop**: CP-SAT
  macro placement + coarse routing, multi-net detailed router, Benders-style
  cuts on failure. Handles arbitrary trees with no layout assumptions; every
  candidate ships with a markdown report and debug SVG (`factopt.report`).
  The loop is **anytime**: the first routed placement becomes the incumbent
  and the remaining time budget keeps searching under a hard
  strictly-smaller-area bound, so more budget monotonically tightens the
  result. Reports record the budget given and the wall time used (total and
  per iteration, master vs routing).
- [x] `loop.optimize_loop(..., fuse=True)` (`dense`) — the same cut loop with
  **direct insertion**: a fusable 2-level single-internal-item chain (e.g.
  copper-cable → electronic-circuit) is packed by `placement.dense.place_dense_row`
  as one cell where the intermediate is inserted machine-to-machine (never
  belted), and only its raws + product are routed as boundary I/O.

Optimizer components:

- [x] `placement.ordering.order_recipes` — ordering that minimizes total
  (flow-weighted) producer→consumer distance, so producers sit next to consumers
  (exact ≤ 8 recipes, CP-SAT beyond).
- [x] `macros` — `MacroCell`/`PortCandidate`/`PlacedMacro`: recipe bands wrapped
  as placeable cells with explicit ports. Items travel on **shared belt trunks**:
  consumers are partitioned into belt-capacity trunks and each trunk is one
  **multi-sink `FlowNet`** (`FlowSink` per consumer). The router grows each
  trunk as a Steiner tree, so the branch topology adapts to whatever geometry
  the master chooses — no pass-through lanes, no fixed visit order, no
  re-chaining between iterations. Splitter cascades at the source appear only
  when an item needs more than one trunk.
- [x] `master` — CP-SAT placement (margin-inflated no-overlap, edge pins, port
  clearance) with a two-stage lexicographic objective (bbox area, then
  rate-weighted **HPWL** over each net's pin set + coarse congestion), plus
  per-net coarse **Steiner flows** (source supplies one unit per sink; used
  arcs count once for congestion/length, mirroring shared trunks) with
  placement-dependent boundary capacities. Macros also get a
  **quarter-turn orientation variable** (`macros.cell.rotated`): bands can face
  any direction, with ports, lanes, inserters, and coarse capacities rotating
  consistently (edge-pinned I/O macros stay fixed). Each **input lane is also
  reversible** (`macros.cell.PortCandidate.reverse`): a per-lane boolean picks
  which end feeds it, so HPWL, port clearance, coarse capacities, and cuts all
  see the chosen side; the router and entity emission flip just that lane's
  belts. This doubles a lane's approach options without rotating the whole cell.
- [x] `routing.multinet` — PathFinder-style negotiated congestion (present +
  history costs) over whole **trees**: a contested net rips up its entire tree
  and re-grows it, targeted rip-up for stragglers, underground cross-capture
  avoidance, and structured `RoutingFailure`s attributed to the failing sink.
- [x] `master.cuts` / `routing.explain` — routing failures become serializable
  cuts (`nogood`, `pin_access`, `corridor`) with human-readable explanations,
  attributed to blocking macros via reachability flooding.
- [x] `validate` — static validator: overlap, bounds, inserter pickup/dropoff,
  and directed belt-path checks (splitter- and underground-aware).

Dense placer:

- [x] `placement.dense.place_dense_row` — **boundary-aware** direct-insertion
  placer: a 2-level single-internal-item chain laid as one horizontal machine
  row, the intermediate inserted machine-to-machine through gap columns, raws +
  product on straight full-width edge lanes. Standalone importable and
  validated; wrapped as a `MacroCell` by the `dense` strategy. (This is the one
  placer the loop uses; the earlier interior-only research placers —
  `place_flow`/`place_belt`/`place_block`/`place_direct` — have been removed.)

### Selection & measurement (done)

- [x] `optimize.optimize` — runs the loop in both flavours (`benders` and
  `dense`), keeps the tightest **complete, target-meeting** block, and reports
  every candidate's footprint (and skip reason) via `.summary()`.
- [x] `sim` — headless-Factorio harness that builds a block, feeds inputs from
  infinity chests, powers it, runs it fast, and reads the output item's real
  production rate. Pure-Python parts are unit-tested; requires Factorio installed
  to actually run.

### Current best results

All results now come from the loop (`benders`/`dense`); the retired hand-rolled
generators are no longer benchmarked.

| Goal | Flavour | Footprint | Notes |
|------|---------|-----------|-------|
| Green science 1/s | `benders` | 19×32 = 608t | best routed steiner run (100 belt tiles); reversible input lanes tightened it below the earlier 609–672t; varies by run |
| Green circuits 20/s | `dense` | 64×17 = 1088t | whole chain fuses to a direct-insertion cell; 35 belt tiles |

The loop is the only path and has no structural layout assumptions; its
footprint is expected to drop as cut families sharpen (corridor min-cuts,
congestion pricing) and margins become failure-driven instead of scheduled.
Multi-consumer items route as **Steiner trees** (one net per trunk, splitters
at junctions), which removes the pass-through-lane geometry constraint and is
the scalable path to more complex, late-game targets where consumers cannot be
chained in a line.

Sample blueprints are checked into `blueprints/` (a `benders` candidate with
its markdown report and debug SVG lives in `blueprints/benders/`).

---

## Known limitations / next steps

- **`benders` is loose and run-to-run variable.** The margin/area-slack
  schedule loosens the whole layout when routing fails; the next step is
  failure-driven spacing (corridor min-cut cuts that widen only the failing
  corridor) and congestion-price cuts on success, so footprints tighten
  instead of ballooning. Master solves are also nondeterministic (parallel
  CP-SAT), so iteration counts vary.
- **Direct insertion works via the `dense` strategy (whole chain *and* sub-chain).**
  `build_problem(fuse=True)` groups recipes into **units**: a fusable
  producer/consumer pair becomes one dense direct-insertion cell, the rest stay
  belt bands. This handles green circuits (the whole plan fuses) and green
  science (only copper-cable → electronic-circuit fuses; gears fan out to the
  belt and inserter bands on belts). With Steiner-tree trunks, green science
  routes with one iron net feeding all four consumers as a single splitter-
  branched tree (~180 belt tiles + 4 splitters vs ~335 belts for the original
  per-consumer fan-out). A geometric finding shaped the cell: the density direct
  insertion buys (removing lanes) is exactly what removes the edge access
  interior machines need for their *other* items, so the dense cell is a single
  row (all machines edge-accessible). Remaining: only single-internal-item pairs
  fuse (no multi-consumer product fan-out from a dense cell yet), and the overall
  loop layout is still loose/irregular — tightness is the Benders-tightening
  roadmap below, not the fusion work.
- **Belt facing needs in-game verification** for the loop output and the sim
  scenario. No layout is in-game-verified yet (the earlier in-game-verified
  `mvp` shared-lane pattern was retired with the old generators). This includes
  **reverse-fed input lanes** (belts flowing east→west across a band, inserters
  picking off them unchanged) — physically standard but not yet confirmed
  in-game.
- **Only input lanes are reversible; output lanes still fan out east.** The
  output splitter cascade (`_fanout_east`) is baked toward the east edge, so a
  product trunk can't yet be collected from either side. Making the fanout
  direction-agnostic is the follow-up that would let the router approach a
  producer's output from either end too.
- **Sim is measurement-only and untested end-to-end here** (no Factorio on the
  dev machine): launch flags, source wiring, and the statistics API call are
  written defensively but flagged for first-run verification.
- **Scope:** single-product blocks, belt-based (no bots), no fluids, higher-rate
  general chains can fail to route (e.g. green science at 2/s).
- **Pluggable master solver; SCIP is not competitive on the full model.** The
  master (placement + coarse routing + cuts) is built against a solver facade
  (`factopt.master.backend`) with two implementations: CP-SAT (default) and
  SCIP via PySCIPOpt (`solve_master(..., backend="scip")`, threaded through
  `optimize_loop`/`optimize` and `scripts/steiner_run.py --backend`). SCIP
  reproduces the model at parity (bilinear `w*h` area as a nonconvex
  constraint; no-overlap, min/max, division, and reified logic as big-M
  linearizations). Benchmarking on green science 1/s
  (`scripts/backend_bench.py`) shows CP-SAT routes a complete block in ~2
  minutes while **SCIP finds no feasible solution to the coarse-routing master
  even at a 20s (or 120s) per-solve limit** -- the big-M reformulation of
  CP-SAT's global constraints is intractable for branch-and-cut at this size.
  SCIP does solve placement-only (`--cell 0`), but slower and only to a
  feasible (not proven-optimal) point. Takeaway: this constraint-heavy,
  pure-integer packing problem is CP's home turf; if a different engine is
  worth trying, a same-paradigm CP solver (CP Optimizer) or a much faster MILP
  solver with native general constraints (Gurobi) is a better bet than SCIP,
  and the two-stage-solve / coarse-routing reformulations are solver-independent
  wins.
- **Objective is still analytical.** Using the sim's measured throughput as the
  search objective is the intended next milestone.

---

## Usage

### Optimize a block (recommended entrypoint)

```python
from factopt.optimize import optimize
from factopt.data import vanilla

res = optimize("logistic-science-pack", 1.0, vanilla.DB)  # green science
print(res.summary())            # per-strategy footprints + the winner
print(res.blueprint_string)     # tightest complete block, paste into Factorio
```

The loop runs several CP-SAT master solves per flavour and can take minutes;
pass `strategies=("dense",)` (or `("benders",)`) to run just one, or tune
`benders_budget_s`.

### The Benders loop directly (report + debug SVG)

```python
from factopt.loop import optimize_loop
from factopt.report import write_candidate
from factopt.data import vanilla

res = optimize_loop("logistic-science-pack", 1.0, vanilla.DB)
print(res.summary())                       # per-iteration story + every cut
write_candidate(res, "out/", "green-science-1ps")  # .blueprint.txt / .report.md / .debug.svg
```

`scripts/steiner_run.py` is a thin CLI over this same call (sweeps the master
time limit / iteration count and writes the artifacts).

### Measure true throughput (headless Factorio)

Requires Factorio installed on the running machine (the harness fails fast
otherwise):

```python
from factopt.sim import SimJob, Source, run_headless

job = SimJob(blueprint_string=bp, output_item="electronic-circuit",
             sources=[Source(0, 3, "copper-plate"), Source(0, 13, "iron-plate")])
result = run_headless(job, factorio_path="/path/to/factorio",
                      scenarios_dir="...", script_output_dir="...")
print(result.output_per_sec)
```

### Just the ratios

```python
from factopt.ratios import solve_ratios
from factopt.data import vanilla

plan = solve_ratios("electronic-circuit", rate=30.0, db=vanilla.DB,
                    assembler="assembling-machine-2")
print(plan)
```

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Draftsman ships Factorio 2.0 game data, so no extra data setup is needed.
