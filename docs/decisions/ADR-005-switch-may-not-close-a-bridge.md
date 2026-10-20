# ADR-005: A switch may not close a bridge under the block

## Status

Accepted — answers #11. Extends `docs/contracts.md` § Board.

## Date

2026-10-20

## Context

§2.5 makes a closed bridge behave like empty space, and fires a switch the moment the block presses
it. Nothing says what happens when the toggle closes the bridge the block is already on — reachable
with a lying block across a soft switch and its adjacent bridge, or with one cube parked on a bridge
while the other presses the switch.

The original game drops the block and restarts the stage. § Board already chose the opposite for
void: *an illegal move is absence, not a losing transition.*

## Decision

The action is not generated. Apply the toggle to `bridges` first; if any occupied cell is then over a
closed bridge, `successors` omits the action. It is a filter, not a code path: `passable(cell,
orientation, bridge_state)` already takes the bridge tuple.

The two readings cannot change a `SearchResult` — a path that presses that switch is dead either way
— so this is provable, not measurable. Given identical results, take the one that preserves "no state
has a cell over a closed bridge" and leaves `Status` three-valued.

## Alternatives Considered

### Generate it and lose — #11's proposal, and what the game does

- Pros: matches the game exactly; the player sees the block fall.
- Cons: creates a state where the block stands on a tile that is not there, which `passable`, the
  key, `is_goal` and the counts must all tolerate. `Status` is `solved | cap | unsolvable` and has no
  `lost` member, so the solver would enqueue a terminal it can never use.
- Rejected: same results, worse invariants. Interactive play is covered below, where it is cheap.

### Persist until the next move

- Cons: the impossible state still exists *and* the next transition needs a special case.
- Rejected.

## Consequences

- Void, closed bridge, fragile and co-occupancy now share one policy in `successors`; the transition
  table gains nothing. Applies to one cube or two — #16 closed on this same policy.
- No benchmark number can move because of this decision, which is why it needed no experiment.
- Interactive play (#28): a player can still press that switch. The renderer asks read-only
  `Board.is_fatal(state, action)` and animates the fall without constructing the state.
- #11's test: a soft switch with an adjacent bridge, block lying across both. That toggle yields no
  successor; the same toggle with the block clear of the bridge is generated, so an over-broad filter
  fails the test.
