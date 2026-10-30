# Mixi-Blox

Bloxorz game and solver — BFS, DFS, UCS, and A* (CSC14003, Project 1).

## Status

The v1 core is frozen and complete: types, stage loader, transition model, and the 10 benchmark
stages in `Source/bloxorz/core/stages/` (provenance in [`CREDITS.md`](CREDITS.md)). The solvers are
in too: a shared search loop (`bloxorz.solvers.base`) with BFS, DFS, UCS and A*. UCS and A* use the
#7 non-uniform cost policy; BFS and DFS use the same loop with a FIFO or LIFO frontier, so BFS
minimises move count while DFS only returns the first goal it reaches. `bloxorz.solvers.ALGORITHMS`
is the registry the game reads: display name -> solver, in Solve-card order.

The Ursina game (#28) — a title screen, level select, playable stages, split-cube control,
undo/retry, a live move/clock HUD, a Solve panel with one card per real algorithm that replays its
path as a movie and reports the run on a card, a results screen and a board framing that survives a
resize — and its headless geometry/controller/catalog/reaction/framing/replay tests, plus the
benchmark harness (#24) with its CSV/JSON/LaTeX and chart exporters, are in place.

Still missing:

- `Report/` holds no measured results yet: `python -m bloxorz.bench.run_all` runs end to end, but
  the charts and tables have not been regenerated from a full run and committed.

## Quick Start (Python 3.11 or 3.12)

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Launch the Game (3D GUI)

The Ursina game launches by default:

```bash
python Source/main.py                       # launch game (title screen & level select)
python Source/main.py --stage <FILE>        # skip menus and play a specific level directly
```

*Key Controls*: `WASD` / Arrow keys to roll, `Z` to undo, `R` to restart, `Tab` to switch cubes (split stages), `Space` to pause replay, `Esc` to quit/back.

### 3. Run Search Solvers (CLI)

Run algorithms headlessly and output JSON `SearchResult`:

```bash
python Source/main.py --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
python Source/main.py --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver astar
python Source/main.py --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver bfs
python Source/main.py --stage Source/bloxorz/core/stages/L1-02_two_flights.json --solver dfs
```

- `--node-cap <int>`: limit expanded nodes.
- `--time-cap <float>`: search deadline in seconds.
- `--no-gui`: inspect stage properties and legal moves in terminal mode without launching the GUI:
  ```bash
  python Source/main.py --no-gui --stage Source/bloxorz/core/stages/L1-01_long_corridor.json
  ```

Exit codes: 0 solved, 1 cap/unsolvable, 2 invalid input or unregistered solver.

### 4. Run Tests & Linter

```bash
pytest -q
ruff check .
```

See the [UCS report and integration notes](docs/ucs_vi.md) and [cost policy](docs/action_cost_vi.md).
The [A* report and proofs](docs/astar_vi.md) cover admissibility, consistency and the teleport fallback.
The [BFS notes](docs/bfs_vi.md) record the move/cost split and the frontier tests.
The [DFS notes](docs/dfs_vi.md) record the DFS-vs-IDS decision and the cycle test.

## Contributing

Work on a branch, PR into `main`. One concern per PR.

- [`docs/contracts.md`](docs/contracts.md) is the spec, and `tests/test_contract.py` enforces the
  layout and import rules. Change a frozen name or signature through the issue that owns that clause
  (§ Ownership), not in passing.
- Put each `Closes #n` on its own line. A comma-separated list closes the first issue only.
- Run `pytest -q` and `ruff check .` before pushing.
