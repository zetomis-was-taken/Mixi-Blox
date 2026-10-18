# v1 Interface Contract

**Status:** draft. The structure and the engine clauses are written; clauses marked *(pending)* are decided in the linked issue and transcribed here verbatim when that issue closes.

This file records decisions, it does not make them. A section changes when the owner named below changes it, and the change links its issue.

## Ownership

| Clause | Decided by | Issue |
| --- | --- | --- |
| State, Action, `successors`, `step_cost`, `cells`, `passable` | TanKhoiTV | #8 |
| Stage format and loader | TanKhoiTV, coordinating #5 / #21 | #8 |
| Solver API and the unsolved result | aFlyingSeal | #31 *(pending)* |
| Stats measurement | Alexvuong2006 | #30 *(pending)* |

## Values

### Cell

```python
Cell = tuple[int, int]  # (row, col), 0-indexed
```

### State

One shape, always. The field set never depends on the value; split-only data is present on every state and `None` when the block is not split. *(pending: field list confirmed with #6's owner, because `key()` is derived from it)*

| Field | Type | Meaning |
| --- | --- | --- |
| `cubes` | `tuple[Cube, ...]` | one entry normally, two when split |
| `bridges` | `tuple[bool, ...]` | one entry per bridge, in stage order |
| `split` | `None \| tuple[Cube, Cube]` | the two cubes when split, else `None` |

```python
Cube = tuple[Cell, ...]  # one cell standing, two cells lying
```

Orientation is derived from the cube's cells, never stored.

### Action

```python
Action = Literal["U", "D", "L", "R"]
```

A path is a `list[Action]`. Solvers return a path only; no animation events, no per-step metadata. The GUI replays the path through `successors`.

## Functions

### Cell access and pivot

```python
def cells(state: State) -> tuple[Cell, ...]: ...
```

The only sanctioned way to ask which cells the block occupies. The pivot is the lexicographically smaller occupied cell, so no consumer re-derives it or depends on iteration order.

```python
def passable(cell: Cell, orientation: Orientation, bridge_state: tuple[bool, ...]) -> bool: ...
```

The only place passability is decided. A cell declares exactly one kind, so passability never has to reconcile two.

### Transitions

```python
def successors(state: State) -> list[tuple[State, Action]]: ...

def step_cost(state: State, action: Action, next_state: State) -> float: ...
```

`successors` is pure and carries no cost. `step_cost` defaults to `1.0` for every action (#7); non-uniform weights are policy, so tuning them never edits engine code. BFS and DFS read only the first; UCS and A\* read both.

### Solver entry point

```python
# (pending) #31 — signature, return type, and the unsolved result
```

Decided by aFlyingSeal in #31. Consumers: #24, the GUI (#28), #21. Transcribed verbatim, not paraphrased.

## Stage

```python
@dataclass(frozen=True)
class Stage:
    id: str
    name: str
    group: str
    grid: tuple[str, ...]
    source: str | None      # URL for transcribed stages, "original" for authored ones
    expected: Expected | None  # fixtures only
```

The loader is the only way a stage enters the program. It derives everything the grid already states: `start`, `goal`, switch positions, `rows`, `cols`. None of those is stored alongside the grid, so the two can never disagree.

| Glyph | Meaning |
| --- | --- |
| `o` | floor |
| `S` | start |
| `G` | goal |
| `X` | fragile |
| `+` | soft switch |
| `H` | heavy switch |
| `=` | bridge |
| `Y` | split switch |

Rules:

- The block starts **standing upright on `S`**. Splitting is a transition (#10), never a second start field — otherwise hand-computed solution lengths are ambiguous.
- Exactly one `S` and one `G`, rectangular grid, every row the same length. Anything else is a loader error.
- The loader raises with file and line on: unknown glyph, ragged rows, missing `S`/`G`, duplicate `S`/`G`, missing `id` or `group`. No defaults, ever.
- `expected.optimal_cost` is allowed only where a solution was hand-computed, and is required for fixtures. It is never derived by running a solver.
- Fixtures are tagged `L1` and count toward the benchmark set (#5), since they double as the first difficulty group (#21).

## Stats

*(pending) #30 — the measurement recipe.*

Agreed contents to carry through: moves and total cost as separate fields; `expanded` counts nodes popped from the frontier; a capped or unsolvable run returns an unsolved result rather than raising.

## Design notes

| Decision | Chosen | Obvious alternative | Why |
| --- | --- | --- | --- |
| Cost model | separate `step_cost` | `successors` returns `(state, action, cost)` | tuning a weight would otherwise edit shared engine code |
| State shape | one shape, split fields always present | optional split fields | a value-dependent field set gives `key()` a runtime-varying arity |
| Pivot | lexicographically smaller cell | per-consumer choice | every off-by-one becomes a silent bug otherwise |
| Cell kinds | one kind per cell | combined kinds | passability stops being a reconciliation problem |
| Stage authority | grid glyphs, everything else derived | store coordinates beside the grid | two sources of truth drift |

## Non-goals

- Animation events or progress reported from inside the search.
- GUI types, or anything the renderer needs beyond `path` and `stats`.
- Solver internals: frontier ordering, visited-set representation, heuristics.
- Cost inside the transition model.
