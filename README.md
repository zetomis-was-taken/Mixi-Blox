# Mixi-Blox

Bloxorz game and solver — BFS, DFS, UCS, and A* (CSC14003, Project 1).

## Status

The v1 core is frozen and complete: types, stage loader, transition model, and the 10 benchmark
stages in `Source/bloxorz/core/stages/` (provenance in [`CREDITS.md`](CREDITS.md)). The Ursina
game (#28) — a title screen, level select, playable stages, split-cube control, undo/retry, a live
move/clock HUD, a results screen and a board framing that survives a resize — its headless
geometry/controller/catalog/reaction/framing tests, and the benchmark harness (#24) with its
CSV/JSON/LaTeX and chart exporters are in place. `pytest -q` runs 130 tests.

Still missing:

- `bloxorz.solvers` (#18-#23). Until `bfs`, `dfs`, `ucs` and `astar` exist, `main.py --solver` is a
  stub and `python -m bloxorz.bench.run_all` exits without running, so `Report/` holds no measured
  results yet.
- Solver playback ("movie mode"): the controller already takes one action at a time, but nothing
  feeds a `SearchResult.path` through the animation yet.


## Contributing

Work on a branch, PR into `main`. One concern per PR.

- [`docs/contracts.md`](docs/contracts.md) is the spec, and `tests/test_contract.py` enforces the
  layout and import rules. Change a frozen name or signature through the issue that owns that clause
  (§ Ownership), not in passing.
- Put each `Closes #n` on its own line. A comma-separated list closes the first issue only.
- Run `pytest -q` and `ruff check .` before pushing.
