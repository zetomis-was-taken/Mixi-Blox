# ADR-004: Void contact is an absent move, not a lost stage

## Status

Accepted — closes #16 as subsumed by #11, and answers #65. Confirms `docs/contracts.md` § Board.

## Date

2026-10-20

## Context

§2.3 makes a move illegal if any cell the block would occupy is void, and §2.5 makes a closed bridge
behave like empty space. § Board draws the consequence: *"an illegal move is absence, not a losing
transition."*

So no move puts one cube over void while the other stands safe. #16's scenario cannot arise, and no
rule is missing. The only remaining route to a half-lost state is a state change that is not an
action — a switch closing a bridge under a cube already standing there — which is #11.

## Decision

No partial-fall rule. Void refusal lives in `successors`, decided by `passable`, and applies to every
cube of a split block. #16 closes as subsumed: whichever answer #11 records applies to one cube and
to the merged block alike.

## Alternatives Considered

### Generate the void move, then lose immediately

#16's proposal.

- Pros: literal — the cube falls off, so the stage is lost like any fall.
- Cons: contradicts §2.3's "illegal (not allowed)", and doubles every split state's branching factor
  with losing edges no winning line reaches.
- Rejected: cost without reachable state.

### Let the surviving cube continue alone

- Pros: forgiving.
- Cons: needs `is_goal` to accept a split state, which §2.4 and §2.5 refuse. Unwinnable, and the
  search cannot prune it.
- Rejected.

## Consequences

- #16 needs no test of its own; its criteria collapse into #11's, and the "presumed" entry flips to
  answered.
- `Status` stays three-valued. Nothing gains a `"lost"` state.
- If #11 chooses "persists until the next move", #16 stays closed — persistence is not "one cube
  falls off".
- #65 asks the same of a split switch whose landing cells are void or a closed bridge. It is a
  refusal, not a fall: the block is never placed, so nothing drops. `Board.outcome` reports
  `refused`, and the action stays absent from `successors` — the reasoning ADR-010 applies to the
  two cases that *are* falls.
