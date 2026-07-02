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
that constrain the next master solve. See
`factorio_blueprint_optimizer_plan.md` for the design rationale.

| Stage | Module | Method |
|-------|--------|--------|
| Ratios / recipe selection | `factopt.ratios` | Linear programming (PuLP/CBC) |
| Macro cells + ports | `factopt.macros` | Band-based cells, splitter fan-out per net |
| Master placement + coarse routing | `factopt.master` | CP-SAT (no-overlap, coarse flows, cuts) |
| Detailed routing | `factopt.routing` | Multi-net negotiated congestion over A\* |
| Cut loop | `factopt.loop` | master → route → explain failures → cuts |
| Static validation | `factopt.validate` | Overlap, bounds, inserters, belt-path flows |
| Evaluation | `factopt.evaluate` | Analytical throughput / bottleneck model |
| Selection | `factopt.optimize` | Try strategies, keep tightest complete block |
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
every recipe tried so far (green circuits, red science, green science), and the
general-purpose Benders loop (`factopt.loop`) places, routes, validates, and
reports candidates with zero layout assumptions. **120 tests pass.**

### Foundations (done)

- [x] **Game data via Draftsman**, pinned to vanilla 2.0. Full fluid-free recipe
  set (not a hand-maintained subset).
- [x] **Blueprint codec** via Draftsman (round-trips; emits valid 2.0 strings).
- [x] **Ratio LP solver** — machine counts + per-item flows for a goal.
- [x] **Analytical evaluator** — resource bill (belts/inserters/power/area) and a
  bottleneck score, with a direct-insertion mode.
- [x] **A\* belt router** — single-commodity, underground-belt aware.

### Placement strategies (done)

Two families exist today: **complete generators** (emit a full importable block,
used by `optimize()`) and **dense placers** (tight interior placement, not yet
wired in — see limitations).

Complete generators:

- [x] `mvp.synthesize` (`compact`) — the tight, in-game-verified **shared-lane**
  pattern. Handles 2-level chains (product = one intermediate + one raw), e.g.
  green circuits and red science; tiles into sub-blocks above one belt lane's
  rate. Smallest footprint where it applies.
- [x] `bus.synthesize_bus` (`bus`) — general **band + A\* routing** generator.
  Handles arbitrary recipe trees and always emits a complete block, but is loose
  (large routing gaps). Now parameterizable by band order and gap sizes.
- [x] `line.synthesize_line` (`line`) — **optimizer-driven** placement: drives the
  `bus` emission from the consumer-adjacency ordering with the tightest gaps that
  still route. Handles general trees; markedly tighter than `bus`.
- [x] `loop.optimize_loop` (`benders`) — the **general-purpose cut loop**: CP-SAT
  macro placement + coarse routing, multi-net detailed router, Benders-style
  cuts on failure. Handles arbitrary trees with no layout assumptions; every
  candidate ships with a markdown report and debug SVG (`factopt.report`).

Optimizer components:

- [x] `placement.ordering.order_recipes` — ordering that minimizes total
  (flow-weighted) producer→consumer distance, so producers sit next to consumers
  (exact ≤ 8 recipes, CP-SAT beyond).
- [x] `macros` — `MacroCell`/`PortCandidate`/`PlacedMacro`: recipe bands wrapped
  as placeable cells with explicit ports; product fan-out via splitter cascades
  so every net is a dedicated port-to-port belt.
- [x] `master` — CP-SAT placement (margin-inflated no-overlap, edge pins, port
  clearance) with a two-stage lexicographic objective (bbox area, then
  rate-weighted flow distance + coarse congestion), plus per-net coarse unit
  flows with placement-dependent boundary capacities.
- [x] `routing.multinet` — PathFinder-style negotiated congestion (present +
  history costs), targeted rip-up for stragglers, underground cross-capture
  avoidance, and structured `RoutingFailure`s.
- [x] `master.cuts` / `routing.explain` — routing failures become serializable
  cuts (`nogood`, `pin_access`, `corridor`) with human-readable explanations,
  attributed to blocking macros via reachability flooding.
- [x] `validate` — static validator: overlap, bounds, inserter pickup/dropoff,
  and directed belt-path checks (splitter- and underground-aware).

Dense placers (interior placement only — no boundary I/O yet):

- [x] `placement.flow.place_flow` — general multi-commodity **vertical
  direct-insertion** slot-grid ILP; minimizes bands. Best for dense, high-rate
  chains (green circuits at 30/s → 5 bands).
- [x] `placement.belt.place_belt` — **belt-lane fan-out** for a single-interior
  2-level chain where one scarce producer feeds many consumers (e.g. red science:
  1 gear → 7 science).
- [x] `placement.cpsat.place_block` — earlier ring-adjacency placer (machines +
  inserters, minimize height); superseded for block synthesis but kept.
- [x] `placement.direct.place_direct[_banded]` — the green-circuit-specific
  flow-coupled model `place_flow` generalizes.

### Selection & measurement (done)

- [x] `optimize.optimize` — runs `compact`, `line`, `bus`, and `benders`, keeps
  the tightest **complete, target-meeting** block, and reports every candidate's
  footprint (and skip reason) via `.summary()`.
- [x] `sim` — headless-Factorio harness that builds a block, feeds inputs from
  infinity chests, powers it, runs it fast, and reads the output item's real
  production rate. Pure-Python parts are unit-tested; requires Factorio installed
  to actually run.

### Current best results

| Goal | Winning strategy | Footprint | Notes |
|------|------------------|-----------|-------|
| Green circuits 5/s | `compact` | 15×14 = 210t | shared-lane |
| Green circuits 30/s | `compact` | 92×14 = 1288t | 2 tiled sub-blocks |
| Green science 1/s | `line` | 41×23 = 943t | `benders` also routes it (~1100–2000t, varies by run) |

`line` still wins green science on footprint; `benders` is the only strategy
with no structural layout assumptions, and its footprint is expected to drop
as cut families sharpen (corridor min-cuts, congestion pricing) and margins
become failure-driven instead of scheduled.

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
- **No direct insertion in general chains yet.** `line`/`bus`/`benders` still
  route intermediates on belts. The consumer-adjacency ordering makes most
  producer→consumer links adjacent (5 of 6 for green science); the next layer is
  emitting those as machine-to-machine **direct insertion** (no through-belt),
  which also fixes the "shared plate/wire lane" contention risk.
- **Dense placers aren't in `optimize()`.** `place_flow`/`place_belt` produce
  tight interiors but don't route **boundary I/O** (raws in, product out), so
  they aren't standalone importable factories. Wiring that in promotes them into
  the selector.
- **Belt facing needs in-game verification** for `bus`/`line`/`belt` and the sim
  scenario. Only the `mvp` shared-lane pattern is in-game-verified so far.
- **Sim is measurement-only and untested end-to-end here** (no Factorio on the
  dev machine): launch flags, source wiring, and the statistics API call are
  written defensively but flagged for first-run verification.
- **Scope:** single-product blocks, belt-based (no bots), no fluids, higher-rate
  general chains can fail to route (e.g. green science at 2/s).
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

`benders` runs several CP-SAT master solves and can take minutes; pass
`strategies=("compact", "line", "bus")` to skip it, or tune `benders_budget_s`.

### The Benders loop directly (report + debug SVG)

```python
from factopt.loop import optimize_loop
from factopt.report import write_candidate
from factopt.data import vanilla

res = optimize_loop("logistic-science-pack", 1.0, vanilla.DB)
print(res.summary())                       # per-iteration story + every cut
write_candidate(res, "out/", "green-science-1ps")  # .blueprint.txt / .report.md / .debug.svg
```

### Tight 2-level blocks directly (`mvp`)

```python
from factopt.mvp import synthesize
from factopt.data import vanilla

res = synthesize(5.0, vanilla.DB)                                    # green circuits
res = synthesize(1.0, vanilla.DB, target="automation-science-pack") # red science
print(res.blueprint_string)
```

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
