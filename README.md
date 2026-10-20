# Mixi-Blox

Bloxorz game and solver — BFS, DFS, UCS, and A* (CSC14003, Project 1).

## Status

`bloxorz.core` is in: the frozen types, the stage loader, the transition model, and 74 tests. The
solvers (#18-#23), the harness (#24) and the GUI (#28) are not. Stages live in
`Source/bloxorz/core/stages/`, and their provenance is in [`CREDITS.md`](CREDITS.md).

## Contributing

Work on a branch, PR into `main`. One concern per PR.

- [`docs/contracts.md`](docs/contracts.md) is the spec, and `tests/test_contract.py` enforces the
  layout and import rules. Change a frozen name or signature through the issue that owns that clause
  (§ Ownership), not in passing.
- Put each `Closes #n` on its own line. A comma-separated list closes the first issue only.
- Run `pytest -q` and `ruff check .` before pushing.
