# Shared search and informed solver design (#7, #18, #22, #23)

## Boundary and scope

`core.costs` owns numeric weights. `Board.step_cost` delegates to it, while transition rules
remain independent. `solvers.base.solve_search` owns the single loop, canonical discovery or
improvement, caps, parent reconstruction and all counts. UCS/A* keep the frozen public API.

FIFO/LIFO ordering remains available through the #18 loop for the BFS/DFS owner to specialize.
There are no separate BFS/DFS solver modules, benchmark harness or chart generation in this branch.
The CLI exposes only the two cost-aware solvers. Tests exercise the generic FIFO/LIFO strategies
without shipping the #19/#20 implementations. The current #18 owner is aFlyingSeal; retain that
issue for their integration review rather than automatically closing it from this handoff.

## Cost and heuristic

For a legal edge, `c = 1 + number of newly occupied fragile cells`. One extra move-equivalent
per contact is a transparent preference to reduce fragile exposure, following the assignment's
example, rather than a probability of failure. Teleport destinations count; stationary cubes
and continued occupancy do not. Ordinary rolls/switches/bridges cost 1 absent fragile contact.
Costs are 1, 2 or 3, so `c_min=1`. Control selection is part of the action, not a separate edge.

Without split switches, `h=c_min*min_occupied_manhattan_to_goal/2`: one roll reduces distance by
at most 2, proving admissibility/consistency under the actual weights. With any split switch,
use zero for the entire stage, including before activation. Inspect the static grid once per
solve, not once per heuristic call. The Vietnamese report contains the full arguments.

## Ordering and counts

FIFO/LIFO discover keys on push; heap ordering `(g+h,g,serial)` allows strictly cheaper paths
to reopen a key, even after expansion. Stale heap entries do not increase expanded. Serial
ties are deterministic and never compare states. All adapters report weighted path cost.
Replay resolves the cube index in the source state, respecting canonical position ordering.

The root is generated once. Generated counts actual pushes; frontier peak includes stale
queued entries. Expanded increases only immediately before successors. Goal testing precedes
the node cap. The time cap follows the existing frozen pseudocode and precedes pop. Contract
prose now explicitly qualifies its goal-before-cap rule as the node cap, without changing API
or pseudocode. The search clock implements a deadline only; measurements live in bench.

## Verification

Tests enumerate 2,946 reachable states across ten official stages, independently compute exact
weighted remaining costs on the reverse graph, check every edge's consistency and all finite
remaining costs for admissibility. Separate graphs force stale entries and reopening under an
admissible inconsistent heuristic; real boards cover weighted path tradeoffs and teleport costs.

The solver returns `Counts`; the future shared harness owns timing, memory and aggregate `Stats`.
No solver reports its own performance. The `perf_counter` in the loop only enforces its deadline.
Run `python -m Source.main` from the root; see README for the exact PowerShell commands.

## Acceptance check

- #7: `c_min=1`, every legal movement has a defined weight, and the heuristic proof uses that
  lower bound. The frozen contract has no separate cube-control action; older issue proposals
  that charge switching are superseded by the cube-indexed action model.
- #22: UCS is heap-ordered by accumulated cost; total cost and path length are distinct.
  Weights live only in `core.costs`, with rationale in the Vietnamese report.
- #23: Manhattan/2 on non-teleport stages, a safe zero fallback for split stages, written
  admissibility/consistency arguments, and exact-remaining-cost tests on the tiny fixtures.
- #18: one generic loop owns discovery/improvement, frontier ordering, counts and caps;
  frozen result records are returned on solved/cap/unsolvable, with no timing/memory metrics.

All four issues are still open on GitHub as of this review. Local implementation evidence is
not a merged delivery. Only #7/#22/#23 are proposed for automatic closure by the eventual PR;
#18 remains a reference for the owner's review.
