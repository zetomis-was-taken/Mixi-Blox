# Project Overview

This is a clone of the game `Bloxorz`, this clone will include:
- Playable version of the game
- The option to solve the game (in a movie way) using various solver algorithms (BFS, DFS, UCS, and A*).

Stack: Python 3.11+ (CI runs 3.11 and 3.12), pytest, ruff, matplotlib, and Ursina for the 3D GUI.
Ursina requires Python `< 3.14` (see `requirements.txt`).

# Project Layout:

```
Source/main.py                 CLI entry point: puts Source/ on sys.path, loads a stage,
                               prints its legal moves; --gui launches the Ursina prototype.
Source/bloxorz/core/           The frozen v1 core (stdlib only).
  contracts.py                 Frozen dataclasses/types: State, Stage, StageIndex, Counts,
                               Stats, SearchResult, Caps; aliases Cell/Cube/Action.
  stage.py                     load_stage(path) -> Stage: schema validation, the six loader
                               rules, and StageIndex compilation (the only way a stage enters).
  engine.py                    Board(stage) transition model: successors, step_cost,
                               passable, is_goal, start, cells/pivot/orientation helpers.
  stages/*.json                10 benchmark stages: L1 plain, L2 fragile, L3 switches,
                               L4 split (two-cube).
Source/bloxorz/gui/            Ursina prototype (issue #28).
  app.py                       Window, camera, HUD, input loop, run() entry.
  board_view.py                One flat tile per non-void cell; bridge tint/height.
  block_view.py                Player boxes and pivot-based roll animation.
  controller.py                Current State; input -> Board.successors; goal callback.
  dot_shader.py                Screen-space halftone shader for tiles and player.
  intro.py                     Load-animation timeline (no Ursina import).
  layout.py                    Pure grid <-> world geometry (no Ursina import).
  parallax.py                  Camera-attached scrolling square backdrop, two depth layers.
  reaction.py                  Which mechanisms the block loads, and how they ease (no Ursina).
  theme.py                     Palette (mapped in docs/gui/theme.md) and animation timing.
Source/bloxorz/bench/          Benchmark harness (issue #24).
  runner.py                    BenchmarkRunner: gc/tracemalloc isolation, 3 runs, medians.
  stats.py                     BenchmarkRecord plus CSV/JSON/LaTeX exporters.
  plots.py                     matplotlib charts (optional import).
  run_all.py                   End-to-end benchmark run; writes into Report/.
Source/bloxorz/solvers/        Planned one-module-per-algorithm package (#18-#23).
                               NOT committed yet: no solve() exists, so bench exits early.
tests/                         pytest suite (contract, stage, engine, GUI layout/controller/
                               intro/reaction, bench smoke) plus tests/fixtures/*.json.
tools/                         transcribe_levels.py (game data -> stage JSON),
                               verify_submission.py (rubric pre-flight, run in CI),
                               package.py (submission ZIP builder).
docs/                          contracts.md (the frozen spec), decisions/ADR-*.md,
                               gui/gui-scaffold.md, gui/theme.md, gui/window.md.
Report/                        LaTeX report; tables/, figures/ and data/ are benchmark outputs.
```

Data flow: stage JSON -> `load_stage` validates and compiles `StageIndex` once, outside the
measured window -> `Board(stage)` is O(1) and answers transitions -> a solver returns
`SearchResult` -> the bench harness measures around `solve()` and builds `Stats`/`BenchmarkRecord`
-> exporters and plots write into `Report/`. The GUI reads `bloxorz.core` only and renders states;
it never re-implements a transition.

# Commands

```bash
pip install -r requirements.txt

pytest -q                                   # full suite (pytest.ini adds Source/ to the path)
ruff check .                                # lint (E, F, I; line length 100)

python Source/main.py --stage Source/bloxorz/core/stages/L1-01_long_corridor.json
python Source/main.py --gui                 # Ursina prototype, boots L1-01
python Source/main.py --gui --stage FILE    # another stage

PYTHONPATH=Source python -m bloxorz.bench.run_all   # fails until bloxorz.solvers exists
python tools/verify_submission.py .         # CI also runs this on every push/PR
python tools/package.py [student_id ...]    # builds the submission ZIP
```

# Conventions

- Changes must be minimal: touch only what the task needs, do not rewrite or reformat unrelated
  code, and leave no scratch files, dead code, or commented-out blocks behind.
- Code must be clean and well-structured: small single-purpose functions, clear names, no
  duplication, and no magic numbers — keep the existing layering and module boundaries intact.
- `Source/` is the package root. Only `Source/main.py` and `pytest.ini` put it on `sys.path`;
  library modules must not do it themselves.
- `docs/contracts.md` is the spec. Names and signatures there are frozen v1: change one only
  through the issue that owns that clause (`§ Ownership`). `tests/test_contract.py` enforces
  layout, import direction, and name/signature rules structurally.
- Layering: `bloxorz.core` imports the standard library only; `bloxorz.gui` and `bloxorz.bench`
  may import `bloxorz.core`; `tools/` scripts may stand alone.
- One stage per JSON file under `Source/bloxorz/core/stages/`. The grid is the only source of
  truth: coordinates, switches, and bridges are validated against its glyphs, and any mismatch is
  a hard `StageError` carrying file and line.
- Tests for GUI logic are headless: never import Ursina in `tests/` (CI installs pytest, not
  Ursina). GUI pose/controller tests use plain objects and fake blocks.
- Use `from __future__ import annotations` and type hints on public functions; keep ruff green
  before pushing.
- Work on a branch and PR into `main`, one concern per PR. Put each `Closes #n` on its own line.
- Stage provenance lives in `CREDITS.md`; add a row there for any new transcribed stage.

# GUI:

Any related things belongs to the game space (ursina) and GUI should be follow by these docs the the folder: `docs/gui`

Quick facts: run with `python Source/main.py --gui`; the prototype boots `L1-01` unless
`--stage` is given. Keys are WASD/arrows (`Tab` swaps the active cube on a split stage), the block
rolls a real quarter-turn, and landing on the
goal currently closes the process (`TODO(#28)`). Camera constants, roll geometry, and known
limitations are documented in `docs/gui/gui-scaffold.md`; palette changes belong in `gui/theme.py`.
