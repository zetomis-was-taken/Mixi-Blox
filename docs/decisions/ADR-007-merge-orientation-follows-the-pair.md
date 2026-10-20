# ADR-007: Merge orientation follows the pair

## Status

Accepted. Answers #14. Records a rule `docs/contracts.md` § Board already states.

## Date

2026-10-20

## Context

§2.5 merges two adjacent cubes into one 1x1x2 block and never says which way the block
lies. The two cells answer it: one row gives a horizontal block, one column gives a vertical one.

## Decision

The pair decides. Two cubes on one row merge lying horizontally, two on one column merge lying
vertically.

A merge costs no action. When a move leaves the cubes orthogonally adjacent, `successors` returns
the merged block as that move's successor and charges that move alone. `Action` never names a merge,
because the player never asks for one.

## Why

Both cells sit in the state already, so the axis is data, not a choice. A fixed orientation cannot
hold those two cells: a vertical pair merged lying horizontally would occupy cells nobody moved to,
for free, without an action. The block would jump. Diagonal pairs stay split, because only
orthogonal adjacency merges.

## Alternatives Considered

### Always lying horizontally

- Cons: a vertical pair lands where the cubes never went, and the engine charges nothing for it.
- Rejected.

### Refuse to merge

- Cons: §2.5 requires the merge, and a split block could never win, since `is_goal` reads
  `standing` and only an unsplit block stands.
- Rejected.

### A merge action

- Cons: charges a move for something the player never performs, and adds work to every split search.
- Rejected.

## Consequences

- `successors` lists the merged `Cube`'s two cells in sorted order, so two routes to the same
  pair give one `key()`.
- No field changes shape at merge, because `cubes` stays a tuple.
- #14's test walks both axes: a row pair merges `lying_h`, a column pair merges `lying_v`.
