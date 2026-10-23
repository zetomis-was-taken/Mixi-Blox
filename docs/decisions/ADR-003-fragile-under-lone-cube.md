# ADR-003: A lone cube does not break a fragile tile

## Status

Accepted — answers #12. Confirms `docs/contracts.md` § Board. Amended by #58: the absent move is
the search-side reading, and the fall §2.5 describes is the render-side one.

## Date

2026-10-20

## Context

§2.5: *"A fragile tile can support the block only when its weight is distributed (the block is
lying). If the block stands on a fragile tile, the tile breaks and the block falls. The block may
safely lie across fragile tiles."*

Read it as weight, not orientation. A lying block puts one unit on each of two cells, a lone cube
puts one unit on one cell, and only `standing` puts two on one. So the cube is the lying block's
load case, and the orientation reading attributes a rule to a sentence that argues from load.

The original game agrees: split pieces cross orange tiles without breaking them, and routing a cube
over fragile ground is how the original levels are solved. § Board already assumes this reading; the
ADR supplies the citation it was missing.

The course FAQ settles it outright. Q16 asks whether a split 1×1×1 cube standing on a fragile tile
breaks it, and the answer is *"Không á em."* (no). That is the instructor answering the exact
question, not an inference from §2.5.

## Decision

Fragile is passable for a lone cube — `passable(f, "cube", …)` is `True`, and nothing is consumed.
For `standing` the move is absent from `successors`, which is the **search-side** reading: no
successor, no edge, and no change to the reachable state set.

The **render-side** reading is §2.5's fall, and `Board.outcome` reports that same action as `fatal`
so interactive play can animate it (#58). These are two readings of one transition, not two rules:
search must never generate a losing edge, and a player must still see the tile break. The decision
this ADR records — a lone cube is safe — is untouched by the amendment.

## Alternatives Considered

### The orientation reading: a lone cube breaks the tile

#12's proposal.

- Cons: the same load is safe spread over two cells and lethal once concentrated into the lighter
  piece. No reading of "weight is distributed" produces that.
- Cons: it protects nothing. The constraint returns on merge, where `f` still refuses a standing
  block, and a lone cube cannot win anyway.
- Rejected: contradicts §2.5 and the original game.

## Consequences

- #12's test: a cube steps onto `f` and survives; a standing block on `f` yields no successor.
- #58: `outcome(state, action).kind` reads `refused` for void and `fatal` for this case, while the
  action stays absent from `successors`. Nothing a solver sees changes, so #21's hand-solved
  stage results stand.
- No contract change was needed for the rule itself — § Board already carried it, and the
  "presumed" entry flips to answered. (#58 later added `outcome` to § Board; the rule did not move.)
- Stages may combine `f` with `Y`: not a shortcut, because the merged block must still stand
  somewhere and fragile refuses it.
