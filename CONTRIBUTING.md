# Contributing

Bloxorz game and solver — BFS, DFS, UCS, A\* (CSC14003, Project 1). Python only, and the search
algorithms are ours to write.

**Work on a branch, PR into `main`.** Keep PRs to one concern; a PR that adds an algorithm and
reorganises the report is two PRs.

## Where things live

The interface contract is frozen: [`docs/contracts.md`](docs/contracts.md). It decides names,
signatures and where modules go. This page is the short version of its § Layout.

```
Source/                      # import root, so: import bloxorz.core.contracts
├── main.py                  # CLI entry point
└── bloxorz/
    ├── core/
    │   ├── contracts.py     # types only: State, Stage, StageIndex, Counts, Stats, SearchResult, Caps
    │   ├── stage.py         # load_stage() — the only way a stage enters the program
    │   ├── engine.py        # Board: successors, step_cost, passable, is_goal
    │   └── stages/          # the stage JSONs
    ├── solvers/             # base.py, then one module per algorithm
    ├── bench/               # experiments harness, exporters, plots
    └── gui/                 # Ursina scene and path replay
tests/                       # pytest, run from the repo root
Report/                      # LaTeX report plus generated figures, tables and data
tools/                       # submission verification and packaging
docs/                        # contracts.md and decisions/
```

## Six rules

1. **`Source/` is the import root.** One place puts it on `sys.path` — the entry point, `pytest.ini`
   and CI — not every module.
2. **`core/` imports nothing from the project.** An `import bloxorz.solvers` inside the engine is
   the one import that must never appear.
3. **Dependencies point one way:** `solvers → core`, `bench → core + solvers`, `gui → core +
   solvers`. Nothing imports `bench` or `gui`.
4. **Each frozen type has one definition**, in `contracts.py`. Do not restate `State`, `Stats`,
   `Counts` or `SearchResult` in your module: import them.
5. **No clocks or allocators outside `bench/`.** Wall time and peak memory are measured *around*
   `solve(stage, caps)`, never inside it: the solver returns counts, the harness measures.
6. **Stage files have one author** — by hand or by one generator, not both. The grid is the only
   source of truth: no `start`, `goal`, `rows` or `cols` fields.

## Before you write code

- **Adding a module?** Put it where the rules above say it belongs. If it fits nowhere, say so on
  the issue before you start rather than after.
- **Changing a frozen name or signature?** Raise it on the issue that owns that clause
  (`docs/contracts.md` § Ownership) and PR the contract with the code, not after it.
- **Implementing a clause?** Read its § Obligations entry first. It names what the loop increments,
  in what order, and what belongs to the harness instead.

## Known traps

Every one of these is live in PR #25. None is a style preference.

- `Source/bloxorz/search/` does not exist. The directory is `solvers/`.
- No `core/` and no `benchmark/` at the repo root, and no `benchmark_results.csv` at the root
  either: harness output goes to `Report/data/`.
- `SearchResult` carries `path` and `counts`. There is no `moves` field and no `stats` field.
- Success is `status == "solved"`, never `len(path) > 0` — a block that starts on the goal has a
  valid empty solution.
- Never commit numbers a mock or fallback solver produced. If a run cannot be reproduced from the
  repo, its output does not go in the report.

## Checks

```bash
python -m pytest          # from the repo root
ruff check .
python Source/main.py --help
```
