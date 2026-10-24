# Mixi-Blox

Bloxorz game and solver — BFS, DFS, UCS, and A* (CSC14003, Project 1).

## Status

The core, shared base, BFS, DFS, UCS and A* are available in this branch. UCS/A* use the #7
non-uniform cost policy and the owner-provided #18 loop; BFS and DFS use the same loop with a
FIFO or LIFO frontier, so BFS minimises move count while DFS only returns the first goal it
reaches. Other solver adapters and GUI remain separate.
Stages live in
`Source/bloxorz/core/stages/`, and their provenance is in [`CREDITS.md`](CREDITS.md).

## Run a solver (Python 3.11+)

```powershell
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver astar
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver bfs
python -m Source.main --stage Source/bloxorz/core/stages/L1-02_two_flights.json --solver dfs
python -m pytest -q
python -m ruff check .
```

The CLI prints a JSON `SearchResult`; moves are `len(path)` and `cost` is weighted total cost.
`--node-cap` limits completed expansions and `--time-cap` sets a search deadline in seconds.
Exit codes: 0 solved, 1 cap/unsolvable, 2 invalid input or unregistered solver.
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
