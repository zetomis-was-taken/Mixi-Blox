# ADR-003: A lone cube does not break a fragile tile

## Status

Accepted — answers #12. Confirms `docs/contracts.md` § Board. Superseded in part by ADR-010, which
separates the search-side absence from the render-side fall; the fragile decision below is
unchanged.

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
For `standing` the move is absent, not losing.

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
- No contract change — § Board already carries the rule, and the "presumed" entry flips to answered.
- Stages may combine `f` with `Y`: not a shortcut, because the merged block must still stand
  somewhere and fragile refuses it.
