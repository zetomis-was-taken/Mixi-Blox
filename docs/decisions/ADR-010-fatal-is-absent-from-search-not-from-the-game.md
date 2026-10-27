# ADR-010: A fatal action is absent from search, not from the game

## Status

Accepted — answers #58. Supersedes ADR-003 in part: the fragile decision it records stands, and what
is added is that its fall is visible.

## Date

2026-10-23

## Context

§2.5 has two ways for a move to be dropped mid-play. A standing block that comes to rest on a
fragile tile breaks it and falls (§2.5, ADR-003), and a switch can close the bridge under the block
(ADR-005). §2.3's refusals are different in kind: void, a closed bridge and a cell already taken are
walls the player never gets past.

Both reach a consumer as the same thing — no entry in `Board.successors` — so nothing downstream can
tell a wall from a loss. `Board.is_fatal` covered only ADR-005, and its own docstring said why:
*"the renderer asks this to animate the fall that interactive play shows. Search never calls it."*
The fragile fall had no equivalent, so a renderer could not tell a broken tile from a wall.

§3.7's feature presentation asks the demo to show a stage being lost, which is #54's last criterion.
That is the consumer: without the distinction there is no loss to show.

The constraint on the answer is that search must not gain an edge. ADR-004 already refused losing
edges for void — *"cost without reachable state"* — and §2.3 reads the same way.

## Decision

`Board.outcome(state, action)` reports which of three things a pressed action does: it moves (with
the successor), it is refused (a wall, no state, because nothing happened), or it is fatal (the
state the fall happens in).

Fatality is therefore a **render-side reading of a search-side absence**, not a property of the
transition model. `successors` keeps only `moves` and ignores the verdict, so the reachable state
set is identical to the one ADR-004 and ADR-005 produced. One private pipeline (`_resolve`) answers
both, so "fatal, and yet absent from `successors`" cannot become false.

The two fatal sites are disjoint by construction. Fragile gives way at the first passability check
and only for a single-cell result, which is what a standing block is. ADR-005's bridge appears only
after the switches fire and only when the bridges changed. A standing piece on fragile occupies no
bridge, and a merge always yields a lying block, which fragile accepts. Fragile is reported `fatal`
and ADR-005 keeps the answer it already had.

The state carried by a `fatal` outcome is a rendering prop, not a state of play: it is exactly a
state `successors` refuses to generate, so expanding it reaches nothing.

## Alternatives Considered

### Keep `is_fatal` and add a second predicate for fragile

- Pros: no new type, and the two existing assertions need not change.
- Cons: one question then needs two calls, and both return `False` for the fragile case — that is
  the ambiguity #58 reports. The predicate is also a hand-copied duplicate of the `_advance`
  pipeline, so the two drift and a fix in one leaves the other wrong.
- Rejected: it answers half of the question, twice.

### Generate the losing edge and let search prune it

- Pros: literal — the tile breaks, so the move is a loss.
- Cons: ADR-004's rejection applies unchanged, since losing edges double the branching factor with
  edges no winning line reaches. It also does not give the renderer what it needs: an edge that a
  solver prunes carries no fall to animate.
- Rejected: the mistake ADR-004 already refused, for the same reason, and it solves neither
  consumer's problem.

### Let the renderer re-derive passability to tell a wall from a fall

- Pros: no engine change at all.
- Cons: the renderer would have to reimplement `passable`, the switch firing and the merge to know
  whether a refusal was fragile-under-standing or a bridge closing. ADR-002 keeps the renderer off
  engine internals precisely so one rule has one implementation.
- Rejected: two implementations of one rule, in the layer least able to test it.

## Consequences

- `successors` output and the reachable state set are unchanged, so #21's hand-solved results stand
  and a fatal action still yields no successor.
- #54 shows a loss and #55 rolls a solver path by reading `outcome`. ADR-002's coarse entry point is
  untouched: it bounds the *solver* boundary, not interactive play, which needs a per-keypress
  transition a solver result cannot give.
- Any future rule that makes an action fatal must now decide *both* readings. #65 is the next one —
  a split teleport whose landing cells are void or a closed bridge, proposed as `refused` because
  both known fatal cases need something to fall onto.
- Tested per outcome on a tiny board, plus one asserting a fatal action is still absent from
  `successors` and one walking a stage to assert the two answers never disagree.
