# ADR-009: A switch's mode is data, not its type

## Status

Accepted. Settles the `action` half of #44. Confirms `docs/contracts.md` § Stage and § Board.

## Date

2026-10-21

## Context

The contract gave a bridge switch the action `toggle` or `permanent`, and the loader forced the word
from the tile: soft is `toggle`, heavy is `permanent`. That reads well until the transcribed levels
arrive. The original game stores a mode per switch-to-bridge link, and it uses all three of them:
`onoff`, `on` and `off`. Level 5 wires three switches to the same two bridges with those three modes,
one each.

## Decision

`Switch.action` is `Literal["toggle", "on", "off"] | None`. A split carries none. Any bridge switch
may carry any of the three. The tile's type decides who fires it, the mode decides what it does: soft
fires on contact, heavy only for a standing block, and `toggle` inverts, `on` opens, `off` closes.

## Why

`permanent` cannot stand in for both one-way modes. Level 11's soft switch carries mode `off` and
drives two bridges that start open, so it closes them; no word in the old vocabulary says that, and
"permanent" is wrong even for the case it names, because another switch can reopen the same bridge.

Deriving the mode from the type was worse than the vocabulary gap: it made the loader reject valid
data. Level 7's heavy switch carries mode `onoff`, so the file failed to load on the type-word rule
rather than on anything about the board.

Three modes cost nothing. All three are stateless functions over `bridges`, so `State` keeps its two
fields, `key()` keeps its arity, and #34 is untouched.

## Alternatives Considered

### Keep `{toggle, permanent}` and map `on` to `toggle`

- Cons: a one-way switch would invert on a second press. Level 11 becomes a different puzzle.
- Rejected.

### Keep the type-derived word, and add a per-level override

- Cons: two sources of truth for one value, and the loader rule survives to fight the data.
- Rejected.

## Consequences

- `Board._fire` reads `switch.action` and calls one helper: `on` sets true, `off` sets false,
  anything else inverts.
- The loader checks only that a split carries no action and a bridge switch carries one.
- Level 11 transcribes without a special case, which is the evidence that the vocabulary is right.
