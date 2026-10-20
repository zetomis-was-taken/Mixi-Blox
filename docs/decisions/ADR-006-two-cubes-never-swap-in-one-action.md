# ADR-006: Two cubes never swap places in one action

## Status

Accepted — answers #13. Confirms `docs/contracts.md` § Board.

## Date

2026-10-20

## Context

§ Board already refuses co-occupancy: actions that place two cubes on one cell are not generated. The
open half is the swap — cube 0 taking cube 1's cell while cube 1 takes cube 0's, so no cell is ever
shared. That is a *compound* action, and `Action` is `tuple[int, Direction]`: one cube, one direction.
§ Board states the model under that type — a lone cube is steered by naming it, and changing control
is free — so the engine moves exactly one cube per action.

## Decision

No swap edge, and no clause for it. A swap cannot appear in `successors`: moving cube 0 into cube 1's
cell is a co-occupancy state under a one-cube-per-action model, and the frozen filter already excludes
it.

It costs nothing, because no rule reads cube identity. Merge reads adjacency, `is_goal` reads
orientation and cell, `passable` reads a cell, `key()` reads the occupied cells. Only `Action` reads
an index, and `Action` is the solver's choice — so every plan containing a swap has an
index-relabelled twin of the same cost: "swap, then move cube 0 left" is "move cube 1 left".

## Alternatives Considered

### Paid swap, cost 1

- Cons: #34 canonicalises `State` by ordering the cubes by cell, so the successor has its parent's
  key — a positive-cost self-loop that can never improve a solution, yet still inflates `generated`.
- Rejected.

### Free swap, cost 0

- Cons: a zero-cost cycle that `step_cost` cannot price. UCS would relax around it forever.
- Rejected.

### Compound action carrying both cubes

- Cons: `Action` cannot express it, and `generated` would then count two moves as one node, against
  § Stats.
- Rejected.

## Consequences

- `successors` needs nothing beyond the frozen filter — no code, no clause, no branch.
- Cube order changes only at split and merge, so #34's ordering is total, not best-effort.
- #13's test covers both halves: a cube cannot enter the other's cell, and two adjacent cubes have no
  successor with the cells exchanged.
- Optimal costs are unaffected, so no experiment was needed.
