# ADR-008: A split switch fires every time

## Status

Accepted. Answers #15. Confirms `docs/contracts.md` § Board, which already makes `Y` inert for a
lone cube.

## Date

2026-10-20

## Context

§2.5 splits the block when it stands on `Y`, and says nothing about a second visit. A block that
splits, merges and returns to `Y` either splits again or remembers that it fired once.

## Decision

`Y` fires every time a standing block lands on it, including after a merge. A lone cube triggers
nothing. The switch teleports the two cubes to `teleport_cubes`, so one position always yields the
same successor.

## Why

Firing once needs a place to keep the flag. `State` holds two fields, `cubes` and `bridges`, and #6
froze that arity, so the flag would add a third and `key()` would grow with it. Two positions that
look identical would then explore differently, and every split search would pay for it.

Firing every time costs nothing. A revisit returns the same split state, and the visited set drops
the duplicate on the strength of `key()` alone.

The split also rides inside the move that lands on `Y`, never as an action of its own, so
`successors` gains no extra edge. Nothing fires at load either: `Y` is a cell kind (#17) and the
start sits on `S`, so one cell is never both.

## Alternatives Considered

### Fire once per stage

- Cons: needs a third `State` field. Identical positions would then differ by history, so `key()`
  must carry the flag and split searches explore up to twice as many states.
- Rejected.

### Let a lone cube fire it

- Cons: a split turns one block into two cubes. One cube cannot become two, so the switch would
  clone it.
- Rejected.

## Consequences

- `successors` reads `teleport_cubes` and returns the split state; nothing reads history.
- A revisit repeats the split and yields a duplicate state, which `key()` already dedups. The
  switch sends the cubes to fixed cells, so nothing loops.
- #15's test splits a block, merges it, walks it back to `Y`, and asserts it splits again.
