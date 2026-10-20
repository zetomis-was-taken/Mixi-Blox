# ADR-006: Two cubes never swap places in one action

## Status

Accepted — answers #13. Confirms `docs/contracts.md` § Board.

## Date

2026-10-20

## Context

§ Board already refuses co-occupancy: *"Actions that would place any cell over void or a closed
bridge, or two cubes on one cell, are not generated."* That settles half of #13.

The open half is the swap — cube 0 taking cube 1's cell while cube 1 takes cube 0's, so no cell is
ever shared. That is a *compound* action, and `Action` is `tuple[int, Direction]`: one cube, one
direction. § Board states the model under that type — a lone cube is steered by naming it, and
changing control is free — so the engine moves exactly one cube per action.

## Decision

No swap edge, and no clause to add for it. A swap is not a distinct action, so it cannot appear in
`successors`: moving cube 0 into cube 1's cell is a co-occupancy state under a one-cube-per-action
model, and the frozen rule already filters it.

This costs nothing, because no rule reads cube identity. Merge reads adjacency, `is_goal` reads
orientation and cell, `passable` reads a cell, `key()` reads the occupied cells. Only `Action` reads
an index, and `Action` is the solver's choice — so any plan containing a swap has an index-relabelled
twin of the same cost: "swap, then move cube 0 left" is "move cube 1 left".

## Alternatives Considered

### A paid swap edge, cost 1

- Cons: #34 makes `State` canonical by ordering the cubes by cell, so the successor has its parent's
  key — a positive-cost self-loop. The one edge shape that can never improve a solution, and it still
  inflates `generated`.
- Rejected.

### A free swap, cost 0

- Cons: a zero-cost cycle, and § Board prices every action from `step_cost` (default `1.0`). UCS would
  relax around it forever.
- Rejected.

### A compound action carrying both cubes

- Cons: `Action` cannot express it, so it becomes a second action type, and `generated` would count
  two moves as one node, disagreeing with § Stats.
- Rejected.

## Consequences

- `successors` needs nothing beyond the frozen filter: no code, no clause, no branch.
- Cube order changes only at split and merge, never by exchange, so #34's canonical ordering is
  cheap: co-occupancy is forbidden, so there are no ties and the ordering is total.
- #13's test covers both halves — a cube cannot enter the other's cell, and two adjacent cubes have
  no successor with the cells exchanged.
- Optimal costs are unaffected: every swapping winner has a swap-free twin of equal length, so no
  experiment was needed to decide this.
