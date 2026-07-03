# The optimization model

This document explains how factopt actually optimizes: the decomposition, the
formulation of each stage, the cut mechanism that ties the stages together, and
the design decisions behind them. It is written for a reader comfortable with
OR concepts (MILP/CP, Benders decomposition, Steiner trees, VLSI place-and-route)
but assumes no familiarity with this codebase. For a tour of the code itself,
see [architecture.md](architecture.md); for the original research survey that
motivated the design, see
[`factorio_blueprint_optimizer_plan.md`](../factorio_blueprint_optimizer_plan.md).

## 1. Problem statement

Given a target item and rate (e.g. 1 logistic science pack per second), produce
a **valid, importable Factorio blueprint**: a set of assembling machines,
inserters, and belts on an integer tile grid that manufactures the target from
raw inputs at the requested rate, minimizing the bounding-box area of the
layout (with routed wirelength as a secondary criterion).

The feasibility side of this problem is unusually rich. A layout is valid only

- if no two entities overlap;
- if every machine's inputs and outputs are served by inserters adjacent to
  belts carrying the right item;
- if every item flow is realized by a *directed, connected* chain of belts,
  underground belts, and splitters, with each belt tile used by exactly one
  flow (belts are not wires — two crossing flows must use an underground);
- if every belt segment's throughput bound is respected.

Discreteness is everywhere (tile positions, 4-way belt directions, 2-tile
splitter geometry, underground length limits), and the coupling between
*where machines go* and *whether belts can be routed between them* is the
crux: a placement that looks compact can be unroutable for purely geometric
reasons that are expensive to express in closed form.

## 2. Decomposition: a logic-based Benders loop

A monolithic model over every tile — placement, belt direction, inserter, and
flow variables together — blows up quickly (this matches the findings of
Patterson et al. on CP models for blueprint generation). Instead, factopt
mirrors an EDA physical-design flow and splits the problem the way chip tools
split placement from routing:

```text
ratio LP                     how many machines of each recipe
   ↓
macro construction           machines grouped into placeable cells with ports
   ↓
┌─ master problem (CP-SAT)   place cells + route coarse flows      ─┐
│                                                                    │  repeat
└─ detailed routing (oracle) instantiate exact belts; on failure,  ─┘
                             emit structured cuts back to the master
   ↓
validation + selection       static checks; keep the tightest block
```

The master is a CP-SAT model that decides discrete placement (positions,
orientations, lane directions) plus a *coarse* routing relaxation. The
subproblem is not an LP — it is a combinatorial router — so no dual cuts
exist; instead, routing failures are *explained* (which macros walled off
which net) and returned as logic cuts in the style of Hooker's logic-based
Benders decomposition. The loop is **anytime**: the first routed placement
becomes an incumbent, and the remaining time budget is spent searching for
strictly smaller placements under a hard area bound.

Two properties make this decomposition workable, and both are deliberate:

1. **The master is optimistic.** Its coarse routing relaxes the true routing
   problem (capacities are optimistic, geometry is binned), so it never rules
   out a routable placement. Optimism is corrected a posteriori by cuts;
   pessimism would silently exclude feasible layouts forever.
2. **The subproblem is a feasibility oracle with attribution.** The router
   does not just fail — it reports *which* net failed, at *which* sink, and
   the explanation pass identifies which placed macros are responsible, so
   cuts can constrain the culprits rather than memorizing whole placements.

## 3. Stage 0: ratios (LP)

`factopt.ratios.solve_ratios` decides *how much of everything* before any
geometry exists. Variables are crafts/second \(r_q \ge 0\) per recipe \(q\)
reachable from the target. For every non-raw item \(i\):

\[
\sum_q \mathrm{net}_q(i)\, r_q \;\ge\; \begin{cases} \text{rate} & i = \text{target} \\ 0 & \text{otherwise,}\end{cases}
\]

where \(\mathrm{net}_q(i)\) is the recipe's production minus consumption of
\(i\) per craft. Raw items (iron plate, copper plate, …) are unconstrained
free inputs — the boundary of the block. The caller can *extend* that boundary
at runtime by naming intermediates as **supplied inputs** (`inputs=` /
`db.with_inputs(...)`): those items are added to the raw set for the run, so
their recipes are never expanded and they enter through west-edge input
connectors like any other raw. This is the lever for keeping deep targets
(e.g. higher science packs, fed pre-built circuits) small enough to place and
route. The objective minimizes total
machine-time \(\sum_q (t_q / s)\, r_q\) (craft time over assembler speed),
which is proportional to machine count. Machine counts are then
\(\lceil r_q t_q / s \rceil\).

With vanilla data and one recipe per item this LP is fully determined; it is
kept as an LP so recipe *selection* (multiple producers per item) can be added
later without restructuring. It is solved once per run with PuLP/CBC in
milliseconds — it is never inside the loop.

## 4. Instance construction: macros, ports, and trunk nets

`factopt.macros.build_problem` turns the ratio plan into the master's input, a
`MacroProblem`: a set of **macro cells** to place, a set of **multi-sink nets**
to route between their ports, and edge-pinning constraints.

### 4.1 Macro cells

A `MacroCell` is a pre-built rectangular layout block: entities in local
coordinates plus **ports** — boundary tiles where one item flow crosses in or
out, each with a required belt direction and a throughput cap. Three kinds
exist:

- **Recipe bands** (`factopt.band`): one recipe's machine row with up to four
  horizontal belt lanes (near/far, above/below the machines) reached by normal
  and long-handed inserters. Input lanes get a west-side port; the output lane
  is extended into an east-side splitter fan-out with one port per outgoing
  trunk (see §4.2).
- **Dense direct-insertion cells** (`factopt.placement.dense`, only with
  `fuse=True`): a fusable producer/consumer recipe pair packed as a single
  machine row where the intermediate item moves machine-to-machine through
  inserter gap columns and is *never belted*. Only the pair's raws and product
  surface as ports. Internally this uses its own small CP-SAT model to order
  producers and consumers in the row such that every consumer is exactly fed
  across its adjacent gaps (a small flow problem on a path graph). Fusion pairs
  are chosen by `plan_fusions`: an internal item with exactly one producer and
  one consumer recipe, validated by test-packing.
- **I/O connectors**: a west-pinned input stub per raw item (with a fan-out
  port per consuming trunk) and an east-pinned output collector for the target.

Pre-baking machine/inserter/lane geometry into cells is a deliberate
coarsening: the master never reasons about individual inserters, only about
rectangles with ports. This is precisely the standard-cell abstraction from
VLSI.

### 4.2 Shared trunks and multi-sink nets

An item produced by one macro may be consumed by several. Rather than one
point-to-point net per (producer, consumer) pair, consumers are partitioned
into **trunks**: bins whose total demand fits a single belt lane's throughput
(first-fit decreasing on demand). Each trunk becomes one **`FlowNet`** with a
single source port and one `FlowSink` per consumer, annotated with rates.

The intent is that the detailed router realizes each trunk as a **Steiner
tree** — one belt leaves the source and reaches every sink, either by branching
to it through a splitter or by running *through* it (§7.1). Because the trunk's
*total* demand fits one belt, every tree edge (which carries only the demand of
the sinks below it) fits too, so no per-edge capacity checking is needed inside
a net. The partition is the only place belt capacity appears as a hard
combinatorial constraint; everything downstream inherits feasibility by
construction.

The order of sinks within a trunk carries no meaning — the router chooses the
branch topology *and* which consumers to string inline from the actual
geometry. This keeps the topology freedom that freed the system from the
earlier pass-through-chaining scheme (where consumers had to be visitable in a
fixed line) while letting the router *recover* a splitter-free pass-by chain
wherever the geometry happens to lay consumers out along one line.

## 5. The master problem

`factopt.master.solve_master` builds and solves the placement + coarse-routing
model. The default engine is CP-SAT; the model is written against a thin
backend facade so it can also be instantiated in SCIP (see §9).

### 5.1 Variables

For each macro \(m\):

- position \((x_m, y_m) \in \mathbb{Z}^2\) on a bounded canvas (default canvas:
  a square with side \(\approx 1.6\sqrt{\sum_m \text{inflated area}}\));
- **orientation**: four Booleans \(o_{m,k}\), \(k \in \{0,1,2,3\}\) quarter
  turns, with \(\sum_k o_{m,k} = 1\), plus an integer channel
  \(\omega_m = \sum_k k\, o_{m,k}\). All four rotated variants of the cell are
  precomputed (entities, ports, and flow directions rotate together), and the
  cell's effective width/height are linear in the \(o_{m,k}\):
  \(w_m = \sum_k o_{m,k} W_{m,k}\). Edge-pinned I/O macros are fixed to
  \(\omega_m = 0\) (their contract is a fixed boundary side);
- **lane reversal**: for each *reversible* input port \(p\) (a lane machines
  only pick from, feedable from either end), a Boolean \(\rho_{m,p}\) choosing
  the reverse end, plus auxiliary products
  \(\rho_{m,p} \wedge o_{m,k}\) since the port's tile depends on both choices.

Global variables: bounding-box dimensions \(W, H\) and the area
\(A = W \cdot H\) (a native integer multiplication in CP-SAT; a nonconvex
bilinear constraint in the MILP backend).

**Port positions as linear expressions.** The tile of port \(p\) on macro
\(m\) is

\[
x^{port}_{m,p} = x_m + \sum_k o_{m,k}\, \xi_{m,p,k} + \sum_k (\rho \wedge o)_{m,p,k} \,(\xi^{rev}_{m,p,k} - \xi_{m,p,k}),
\]

with constants \(\xi\) read off the rotated cell variants (and similarly for
\(y\), and for the *access tile* one step outside the footprint). Everything
downstream — wirelength, coarse routing endpoints, clearance, pin-access cuts
— is written against these expressions, so orientation and lane reversal are
first-class decisions visible to every part of the model rather than a
post-processing step.

### 5.2 Constraints

- **No-overlap with routing margin.** Each rectangle is inflated by `margin`
  tiles and the inflated rectangles must be pairwise disjoint (CP-SAT's 2-D
  no-overlap global over interval variables), guaranteeing at least `margin`
  tiles of belt corridor along some separating axis between any two macros.
  The margin is a *scheduled* parameter of the loop, not a constant (§8).
- **Containment**: \(x_m + w_m \le W\), \(y_m + h_m \le H\).
- **Port clearance.** A port's access tile must lie inside the bounding box
  with one further tile beyond it, so the router can approach the port mouth
  from the side rather than only head-on down a 1-wide dead end. Since port
  sides depend on orientation, these are reified per orientation variant; for
  reversible ports, clearance is reserved for *both* possible ends regardless
  of which the solver picks (a conservative simplification that costs a little
  area and saves a quadratic number of reified terms).
- **Edge pins.** Raw-input connectors satisfy \(x_m = 0\) (west); the output
  collector satisfies \(x_m + w_m = W\) (east).
- **Benders cuts** accumulated from previous iterations (§7).
- **Incumbent bound.** When the loop already holds a routed solution,
  \(A \le A^{inc} - 1\): the master may only return strictly smaller
  placements.

### 5.3 Objective: two-stage lexicographic

The master solves twice per invocation:

1. **Stage 1 — area.** Minimize \(A\). Let \(A^\*\) be the best value found
   within the time limit.
2. **Stage 2 — wirelength + congestion.** Add
   \(A \le \lfloor (1+\sigma) A^\* \rfloor\) (\(\sigma\) is the loop's
   `area_slack`, trading footprint for routability) and minimize

\[
\underbrace{\sum_{n \in \text{nets}} \lceil 100\, r_n \rceil \cdot \mathrm{HPWL}(P_n)}_{\text{flow-weighted wirelength}}
\;+\; \underbrace{500 \sum_{e} \mathrm{sat}_e \;+\; 2 \sum_{n,a} u_{n,a}}_{\text{coarse congestion + tree length (§6)}}
\]

where \(P_n\) is the pin set of net \(n\) (source port plus every sink port),
\(r_n\) its rate in items/s, and HPWL the half-perimeter of the pins' bounding
box — computed with min/max equalities over the port coordinate expressions.
HPWL is the standard placement proxy for Steiner-tree length: exact for 2–3
pins, a lower bound beyond, and cheap enough to sit in the inner objective.
Rates are scaled by 100 into integers, which also sets the unit for the
congestion weights (a saturated coarse edge "costs" 5 tiles of a 1 item/s
net's detour).

If stage 2 times out without a feasible solution, the stage 1 solution is
kept — lexicographic order is preserved and the loop still gets a placement
to try routing.

## 6. Coarse routing inside the master

Placement quality alone (even with margins and HPWL) says nothing about
whether flows can *collectively* get through the gaps between macros. The
coarse-routing extension (`factopt.master.coarse`) adds a binned relaxation of
the routing problem directly to the master model, so the master avoids
placements whose flows would have to squeeze through walls.

### 6.1 Steiner flows on a binned grid

Overlay the canvas with a grid of \(g \times g\)-tile cells (default
\(g = 4\)); adjacent cells are connected by directed arcs. For each net \(n\)
with \(k_n\) sinks:

- integer flow \(f_{n,a} \in [0, k_n]\) per arc;
- a Boolean \(u_{n,a} = \mathbb{1}[f_{n,a} > 0]\) ("net \(n\) uses arc
  \(a\)"), linked by \(f \le k u\) and \(u \le f\);
- conservation at every cell \(c\):

\[
\sum_{a \in \delta^+(c)} f_{n,a} - \sum_{a \in \delta^-(c)} f_{n,a}
= k_n \cdot \mathbb{1}[\mathrm{src}_n \in c] - \sum_{s \in \mathrm{sinks}(n)} \mathbb{1}[s \in c].
\]

The source supplies one unit per sink and each sink consumes one, but
**capacity and cost count \(u\), not \(f\)** — an arc used by a net counts
once no matter how many sinks sit downstream of it. This is the classical
single-commodity flow relaxation of the Steiner tree, and it exactly mirrors
the detailed router's shared-trunk semantics: one physical belt crosses a
boundary once regardless of fan-out behind it.

The crucial twist versus routing on a fixed instance: the source and sink
indicators are themselves *decision-dependent*. Each pin's coarse cell is
\(\lfloor x^{port}/g \rfloor\) (an integer division constraint on the port
expression from §5.1), one-hot encoded into per-cell Booleans. The master is
therefore genuinely optimizing placement and coarse routing jointly, including
orientation and lane-reversal effects on where flows enter the grid.

### 6.2 Placement-dependent capacities

The capacity of the boundary between two adjacent cells starts at \(g\) (one
belt per boundary tile) and shrinks by the extent to which placed macros
*span* it:

\[
\mathrm{cap}_e = \max\Bigl(0,\; g - \sum_m \mathrm{spans}_{m,e} \cdot \mathrm{overlap}_{m,e}\Bigr),
\]

where \(\mathrm{spans}_{m,e}\) is a reified Boolean (macro \(m\) covers tiles
on *both* sides of the boundary line) and \(\mathrm{overlap}_{m,e} \in [0,g]\)
is the length of the macro's intersection with the boundary segment (built
from min/max constraints on the macro's placement variables). The shared
constraint per undirected edge \(e = \{c_1, c_2\}\) is

\[
\mathrm{used}_e = \sum_n \bigl(u_{n,(c_1,c_2)} + u_{n,(c_2,c_1)}\bigr) \le \mathrm{cap}_e .
\]

This capacity model is deliberately **optimistic**: a macro whose wall merely
*touches* a boundary does not consume capacity (routes can run along walls),
only macros that straddle it do. Per the decomposition contract (§2),
optimistic errors are recoverable through cuts; pessimistic ones are not.

A Boolean \(\mathrm{sat}_e = \mathbb{1}[\mathrm{used}_e \ge \mathrm{cap}_e]\)
feeds the stage-2 objective, pricing *fully utilized* boundaries before they
become detailed-routing failures, and \(\sum u\) adds a small coarse
tree-length term. The extracted coarse routes are also handed to the detailed
router as soft guidance (§7.1).

## 7. The subproblem: detailed routing as an oracle

Given a concrete placement, `factopt.routing.multinet.route_nets` must realize
every net as a physically buildable belt tree — or fail with structure. It has
no relaxations left: exact tiles, exact belt directions, exact splitter and
underground-belt geometry.

### 7.1 One net: Steiner tree growth

`routing.steiner.route_tree` grows a single net's tree on the tile grid:

- The **trunk** is routed from the source port's access tile to the *farthest*
  sink with a direction-aware A\* over states (tile, heading), supporting
  underground belts (with span-conflict tracking so two undergrounds cannot
  cross-capture each other) and a turn penalty.
- Every subsequent sink connects **Prim-style** (nearest-to-tree first) via a
  *multi-source* A\*: the search is seeded with one candidate **splitter
  junction** per straight belt of the existing tree. Tapping a straight belt
  tile \(T\) flowing in direction \(d\) means replacing it with a 2-tile
  splitter covering \(T\) and one of its perpendicular neighbours; the old
  continuation stays fed and the branch exits from the second half. Corners,
  underground endpoints, port mouths, and existing splitters can never be
  tapped. The search itself picks the cheapest tap point, so the branch
  topology is an emergent property of the geometry, not an input.
- **Pass-through lanes (serving a sink without a splitter).** A splitter is not
  the only way to serve a consumer. A machine only *picks* off its input lane,
  and that lane spans the whole cell (the reversible-lane geometry of §5.1), so
  a belt can run straight *into* the consumer's lane and out the far edge — the
  machine takes its share off the passing belt and the remainder continues to
  the next sink. This is exactly balanced because the trunk's total demand fits
  one belt: each consumer removes its rate and the chain's terminus consumes the
  rest. The router models this as a special A\* move: when a search reaches a
  consumer's access tile it may place a belt feeding the lane and *jump* to the
  lane's far-side exit tile (`PlacedMacro.port_through_exit`), continuing the
  search from there. A run-through costs a small `through_cost` while a splitter
  tap costs a larger `splitter_cost`, so the A\* prefers threading a consumer
  that lies on its path and only spends a splitter where the flow must actually
  diverge. The result is a **hybrid tree**: colinear consumers are strung onto
  one pass-by run (zero splitters), divergent ones branch. Connectivity is the
  correctness contract — a run-through consumer is an interior node whose exit
  must feed onward, and the static belt-path check (§7.3) verifies every sink is
  reached, so a dead-ended pass-through cannot slip through.
- If some sink is unreachable under the farthest-first trunk order, alternate
  trunk targets are retried (each sink once) — a trunk squeezed through a
  1-wide corridor can make junctions impossible for one order but not another.
  A net is all-or-nothing; on failure the router reports the *index of the
  failing sink*, which is what cut attribution keys on.

### 7.2 Many nets: negotiated congestion

Nets compete for tiles. The multi-net layer runs PathFinder-style negotiated
congestion, the standard FPGA routing scheme, adapted to whole trees:

- Every tile has a **present cost** (per current foreign occupant; base 6,
  growing ×1.5 per round) and a **history cost** (+2 each round the tile stays
  contested). Tiles off the net's coarse-route cells get a mild extra cost
  (0.4), pulling detailed routes toward the master's coarse plan without
  forbidding detours.
- Round 0 routes every net against soft costs. Afterwards, only nets actually
  in conflict are ripped up **whole-tree** and re-grown; settled trees stay
  put, which prevents pairs of nets from endlessly swapping channels.
- Nets are processed heaviest-rate-first (then largest pin spread), so
  high-value trunks claim geometry early.
- After the round limit (24), two escalations run: a **hardening pass**
  (re-grow remaining conflicted nets sequentially with all other trees as hard
  obstacles) and a **targeted rip-up** (compute a straggler's ideal tree on
  the empty grid, evict exactly the nets sitting on it, route the straggler
  first, re-route the victims; revert if the exchange made things worse).

Failures are classified with attribution: `no_path` (unreachable even alone on
the grid), `congestion` (couldn't converge), `port_blocked` (an endpoint tile
is inside an obstacle or out of bounds), and `port_conflict` (two ports' access
tiles coincide — no negotiation can fix a shared mouth tile). Each failure
carries the net, the failing sink, and contested tiles.

### 7.3 Static validation

A routed candidate passes `factopt.validate` before becoming the incumbent:
tile-exclusive occupancy, bounds, inserter pickup/dropoff sanity, belt
chaining (every belt feeds a belt/splitter/underground), and a directed
belt-path check from every net's source to each sink (splitter- and
underground-aware). This is a redundant safety net below the router — the
router should never emit an invalid tree, and validation catches it if it
does.

## 8. Cuts and the loop

### 8.1 Cut families

`routing.explain.explain_failures` converts failures into `BendersCut`s;
`master.cuts.apply_cuts` compiles them into the next master model. Every cut is
serializable and carries a human-readable explanation, so a run log tells the
story of why placements moved. Three families:

- **`pin_access`** — from `port_conflict`: two ports' access tiles must not
  coincide,
  \((x^{acc}_a - x^{acc}_b \ne 0) \lor (y^{acc}_a - y^{acc}_b \ne 0)\),
  written against the access-tile *expressions*, so it is valid under every
  orientation and lane-reversal choice. This is the one family that is a
  globally sound constraint on the true feasible set.
- **`corridor`** — from `no_path`/`port_blocked`/`congestion`: a no-good over
  the *responsible subset* of macros. Attribution floods the free tiles
  reachable from the failed net's start (including underground jumps) and
  collects the macros owning the frontier — the actual walls of the dead end.
  For congestion, macros adjacent to the contested tiles are collected
  instead. The cut is
  \(\bigvee_{m \in S} (x_m \ne \hat{x}_m \lor y_m \ne \hat{y}_m \lor \omega_m \ne \hat\omega_m)\):
  at least one involved macro must move or turn.
- **`nogood`** — the same disjunction over the full macro set, used only as a
  fallback when no structured explanation is available; it merely forbids
  exact repetition.

A note on soundness: a subset no-good generalizes across the positions of
*uninvolved* macros — that is its entire value, one cut kills a whole family
of placements — but it is heuristic, since in principle some placement it
excludes could have been routable thanks to an uninvolved macro differing.
The system accepts this trade (attribution is careful, and the loss is a
corner case) in exchange for cuts that actually bite. Positions are integers,
so `≠` literals make each cut a single Boolean clause over reified
comparisons — cheap for CP-SAT.

### 8.2 The loop: feasibility phase, then tightening phase

`factopt.loop.optimize_loop` orchestrates master and oracle under a wall-clock
budget (default 240 s total, 20 s per master solve, ≤ 8 iterations):

**Feasibility phase.** Iterations walk a loosening schedule of
\((\text{margin}, \text{area\_slack})\) rungs:

```text
(1, 0.0) → (1, 0.15) → (2, 0.15) → (2, 0.3) → (3, 0.3) → (3, 0.5) → (4, 0.5) → (4, 0.7)
```

Cuts alone cannot always fix infeasibility — if every tight placement is
unroutable, the master needs *room*, not just prohibitions. Widening margins
and letting stage 2 trade area for shorter routes is the "minimize
infeasibility first" lever. Orientation freedom means the master can keep
producing fresh tight-but-congested layouts at a given rung, which is why the
ladder ends in a roomy fallback.

**Tightening phase.** The first routed placement becomes the incumbent and
routing success *does not* end the loop. Subsequent masters carry
\(A \le A^{inc} - 1\), so any returned placement is strictly smaller; each new
routed solution replaces the incumbent. Rather than freeze the rung that first
routed, an **adaptive controller** chases the tightest rung that still routes:

- a **routing success** biases one rung *tighter* (less area slack, then less
  margin) — actively drive toward the tight regime instead of lingering where
  the first placement happened to route;
- an **unroutable** placement loosens one rung (give the router more room at
  the same area cap) while its cut forbids the exact repeat;
- **master-infeasibility** (nothing smaller fits at this margin) steps to a
  *tighter* margin, which admits smaller areas; the loop stops when the
  tightest rung is exhausted or the budget runs out.

Because the area cap only ever shrinks (each incumbent is strictly smaller),
this controller converges, and more budget monotonically tightens the result.
This replaced an earlier design in which the tightening phase kept the rung
that first routed and only decremented the margin — a **one-way ratchet**: if
an early tight-slack placement failed to route (sensitive to master
nondeterminism and to router quality), the loop loosened to a higher slack and
was *stranded* there for the rest of the budget, never re-tightening slack.
That single dynamic explained most of the run-to-run footprint variance.

`start_loose` seeds the feasibility phase at a moderately roomy rung (not the
loosest: a large margin makes the master's stage-1 area minimization
intractable within a per-solve time limit, so the incumbent lands bloated and
tightening crawls). Runtime `max_w`/`max_h`/`max_area` caps apply to every
solve (folded together with the incumbent bound, tighter wins), so a caller can
ask "does this route inside a known footprint?".

Cuts accumulate across both phases and across rungs; a cut derived at margin 2
still validly excludes the same geometric failure at margin 1.

### 8.3 Selection

`factopt.optimize.optimize` runs the whole loop twice — `benders` (belt-only)
and `dense` (with direct-insertion fusion) — and keeps the tightest candidate
that is complete, validated, and target-meeting. Since nets are dedicated
belts sized by the ratio plan, a fully routed and validated block meets the
target analytically; measured-throughput scoring via the headless-Factorio
harness (`factopt.sim`) is the intended next objective upgrade.

## 9. Why CP-SAT (and what the SCIP experiment showed)

The master is a pure-integer, constraint-heavy packing problem: 2-D
no-overlap, min/max/division equalities, Boolean products, and a large amount
of reified logic (orientation guards, capacity reification, cuts). This is
constraint programming's home turf, and CP-SAT's clause learning plus a
parallel solve portfolio suit the two-solve lexicographic pattern well.

The model is nevertheless built against a solver facade
(`factopt.master.backend`) with a CP-SAT and a SCIP implementation at feature
parity — the SCIP backend linearizes the global constraints with big-M and
handles \(W \cdot H\) as a nonconvex bilinear term. Benchmarking on green
science 1/s: CP-SAT routes a complete block in about 2 minutes, while SCIP
finds **no feasible solution** to the placement + coarse-routing master even
at generous per-solve limits, and solves placement-only slower and without
proving optimality. The takeaway recorded in the README: the big-M
reformulation of CP-SAT's globals is intractable for branch-and-cut at this
size; if another engine is worth trying, it is a same-paradigm CP solver or a
MILP solver with native general constraints, and the reformulations that
matter (two-stage solve, coarse routing) are solver-independent.

## 10. Known relaxation gaps and open ends

Honest inventory of where the model is weaker than the true problem, and what
that costs:

- **Subset no-goods are heuristic** (§8.1) — accepted trade for
  generalization.
- **Coarse capacities are optimistic by design** (§6.2); recoverable via
  cuts, but each recovery costs an iteration. Sharper families (corridor
  min-cut cuts that widen only the failing corridor, congestion pricing on
  *success*) are the planned replacement for the blunt margin schedule, which
  currently loosens the whole layout when routing fails.
- **The margin schedule is global**, not failure-driven: one congested
  corridor inflates spacing everywhere.
- **HPWL underestimates Steiner length** beyond 3 pins — standard and mostly
  harmless, since coarse routing supplies the topology-aware signal.
- **Cuts key on \((x, y, \omega)\) but not lane reversal**, so a failure
  caused purely by a lane-direction choice is only excluded jointly with its
  placement.
- **The router is sequential/greedy within a net** (farthest-first trunk with
  fallback orders) and negotiation-based across nets: a feasibility heuristic,
  not exact. A placement can be declared unroutable that a smarter router
  would route; the resulting cut then over-constrains the master. In practice
  the escalation ladder (negotiation → hardening → targeted rip-up) makes
  this rare. The splitter-vs-pass-through choice (§7.1) is part of this greedy
  search — A\* takes the locally cheaper option per sink inside a single tree
  grow, so a tree is a good hybrid, not a globally minimal mix of the two.
- **Rates are handled entirely by construction** (trunk partition + dedicated
  belts), never as routing constraints — clean, but it forbids deliberately
  merging compatible flows onto one belt.
- **Master nondeterminism**: the parallel CP-SAT portfolio makes iteration
  counts and final footprints vary run to run.
