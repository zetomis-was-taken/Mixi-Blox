# Mixi-Blox

Bloxorz game and solver — BFS, DFS, UCS, and A* (CSC14003, Project 1).

## Status

The engine, stage loader, shared search loop (#18), UCS (#22), and A* (#23) run from the CLI.
FIFO/LIFO adapters exercise the same loop as BFS/DFS integration baselines; coordinate their final
adoption with the owners of #19/#20. The GUI (#28) and full-team harness (#24) remain separate work.
Stages live in `Source/bloxorz/core/stages/`; provenance is in [`CREDITS.md`](CREDITS.md).

## Run and verify (Python 3.11+)

From the repository root, in PowerShell:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m ruff format --check Source/bloxorz/solvers Source/bloxorz/core/costs.py Source/bloxorz/bench/informed_search.py Source/main.py tests/test_cost_search.py tests/test_search_integration.py tests/test_cost_policy.py tests/test_informed_measurement.py
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
python -m Source.main --stage Source/bloxorz/core/stages/L4-01_split_into_the_far_room.json --solver astar --node-cap 100000
```

The CLI prints a JSON `SearchResult`. Exit codes are 0 for solved, 1 for cap/unsolvable, 2 for invalid
input. `--time-cap` sets a search deadline in seconds; `--node-cap` limits completed expansions.
The engine/search CLI needs only the standard library. Development dependencies add tests and plots.

## UCS/A* measurements and report

```powershell
$env:PYTHONPATH = 'Source'
python -m bloxorz.bench.informed_search --markdown docs/informed_search_results_vi.md
```

This separate handoff tool takes three isolated runs per algorithm-stage pair and validates every
returned path. It writes raw CSV/JSON to `Report/data/informed_search/`, PNG/SVG plots to
`Report/figures/informed_search/`, and the measured table linked below. Raw outputs are ignored by
Git and can always be regenerated; no output goes in the assignment-document directory.

- [Cost/search design and integration notes](docs/informed_search_design.md)
- [Vietnamese UCS/A* report section](docs/report_ucs_astar_vi.md)
- [Measured comparison table](docs/informed_search_results_vi.md)
- [Handoff and proposed PR description](docs/informed_search_handoff.md)

These measurements use the local FIFO/LIFO adapters for comparison. The full-team report should
rerun its harness when the final BFS/DFS and GUI branches are integrated.

## Contributing

Work on a branch, PR into `main`. One concern per PR.

- [`docs/contracts.md`](docs/contracts.md) is the spec, and `tests/test_contract.py` enforces the
  layout and import rules. Change a frozen name or signature through the issue that owns that clause
  (§ Ownership), not in passing.
- Put each `Closes #n` on its own line. A comma-separated list closes the first issue only.
- Run `pytest -q` and `ruff check .` before pushing.
