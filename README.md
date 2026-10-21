# Mixi-Blox

Bloxorz game and solver — BFS, DFS, UCS, and A* (CSC14003, Project 1).

## Status

The engine, stage loader, non-uniform cost policy (#7/#22), shared search loop (#18), UCS (#22),
and A* (#23) are implemented. The CLI exposes UCS and A*. The shared loop retains FIFO/LIFO
extension points for the BFS/DFS owner, without separate BFS/DFS solver modules in this branch.
The GUI, benchmark harness and experiment charts remain with their respective workstreams.
Stages live in `Source/bloxorz/core/stages/`; provenance is in [`CREDITS.md`](CREDITS.md).

## Run and verify (Python 3.11+)

From the repository root, in PowerShell:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m ruff format --check Source/bloxorz/solvers Source/bloxorz/core/costs.py Source/main.py tests/test_cost_search.py tests/test_search_integration.py tests/test_cost_policy.py tests/test_cli.py
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
python -m Source.main --stage Source/bloxorz/core/stages/L4-01_split_into_the_far_room.json --solver astar --node-cap 100000
```

The CLI prints a JSON `SearchResult`. Exit codes are 0 for solved, 1 for cap/unsolvable, 2 for invalid
input. `--time-cap` sets a search deadline in seconds; `--node-cap` limits completed expansions.
The engine/search CLI needs only the standard library. Development dependencies add tests and lint.

## UCS/A* design and report

- [Cost/search design and integration notes](docs/informed_search_design.md)
- [Vietnamese UCS/A* report section](docs/report_ucs_astar_vi.md)
- [Insertable LaTeX sections and template integration notes](Report/sections/informed_search_integration.md)
- [Local issue checklist and ownership boundaries](docs/informed_search_task_checklist.md)
- [Handoff and proposed PR description](docs/informed_search_handoff.md)

The Vietnamese report covers the cost policy, UCS/A*, heuristic proofs and shared-loop semantics.
Performance tables and plots belong to the later full-team experiments work.

## Contributing

Work on a branch, PR into `main`. One concern per PR.

- [`docs/contracts.md`](docs/contracts.md) is the spec, and `tests/test_contract.py` enforces the
  layout and import rules. Change a frozen name or signature through the issue that owns that clause
  (§ Ownership), not in passing.
- Put each `Closes #n` on its own line. A comma-separated list closes the first issue only.
- Run `pytest -q` and `ruff check .` before pushing.
