# Shared search and informed solver design (#7, #18, #22, #23)

## Boundary and scope

`core.costs` owns numeric weights. `Board.step_cost` delegates to it, while transition rules
remain independent. `solvers.base.solve_search` owns the single loop, canonical discovery or
improvement, caps, parent reconstruction and all counts. UCS/A* keep the frozen public API.

FIFO/LIFO adapters demonstrate #18 integration for BFS/DFS. Coordinate their adoption with the
#19/#20 owner; they do not claim that member's allocated work. `bench.informed_search` is a
separate handoff measurement tool, not a replacement for #24. No existing harness is overwritten.

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

## Verification and measurements

Tests enumerate 2,946 reachable states across ten official stages, independently compute exact
weighted remaining costs on the reverse graph, check every edge's consistency and all finite
remaining costs for admissibility. Separate graphs force stale entries and reopening under an
admissible inconsistent heuristic; real boards cover weighted path tradeoffs and teleport costs.

Load once outside measurement. Each pair has three isolated calls with GC and a fresh/reset
tracer; time surrounds solve only, cleanup is in finally, replay follows measurement. Require
identical full results across repetitions. Time and peak bytes have independent medians. Caps
and unsolvable keep measured work but print no solution cost/length. Exceptions keep an error
message and missing metrics. Raw samples and environment/source fingerprints accompany CSV.

Run `python -m Source.main` from the root. Set `PYTHONPATH=Source` for
`python -m bloxorz.bench.informed_search`. See README for exact PowerShell commands. Generated
raw files/plots are ignored and never go in the assignment-document directory.
