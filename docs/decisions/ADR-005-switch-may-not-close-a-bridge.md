# ADR-005: A switch may not close a bridge under the block

## Status

Accepted — answers #11. Extends `docs/contracts.md` § Board.

## Date

2026-10-20

## Context

§2.5 makes a closed bridge behave like empty space, and fires a switch the moment the block presses
it. It does not say what happens when the toggle closes the bridge the block is already on — possible
with a lying block across a soft switch and its adjacent bridge, or one cube parked on a bridge while
the other presses the switch.

The original game drops the block and restarts the stage. § Board already chose the opposite for void:
*an illegal move is absence, not a losing transition.*

## Decision

The action is not generated. Apply the toggle to `bridges` first; if any occupied cell is then over a
closed bridge, `successors` omits it. A filter, not a code path: `passable(cell, orientation,
bridge_state)` already takes the bridge tuple.

Either reading gives the same `SearchResult` — a path that presses that switch is dead either way — so
this is provable, not measurable. With results identical, take the one that keeps "no state has a cell
over a closed bridge" and leaves `Status` three-valued.

## Alternatives Considered

### Generate it and lose — #11's proposal, and what the game does

- Pros: matches the game; the player sees the block fall.
- Cons: needs a state where the block stands on a tile that is not there, which `passable`, `key()`,
  `is_goal` and the counts must all tolerate. `Status` has no `lost` member, so the solver would
  enqueue a terminal it can never use.
- Rejected: same results, worse invariants. Interactive play is covered below, where it is cheap.

### Persist until the next move

- Cons: the impossible state still exists *and* the next transition needs a special case.
- Rejected.

## Consequences

- One filter in `successors`; the transition table gains nothing. Void, closed bridge, fragile and
  co-occupancy share one policy, which is why #16 closed without a rule of its own.
- No benchmark number can move because of this, so it needed no experiment.
- Interactive play (#28): the player can still press that switch. The renderer asks read-only
  `Board.is_fatal(state, action)` and animates the fall without constructing the state.
- #11's test: block across a soft switch and its bridge yields no successor, while the same toggle
  with the block clear is generated — so an over-broad filter fails it.
