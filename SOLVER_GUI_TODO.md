# Solver Replay — what's left

The GUI side is done: Solve panel, replay driver, HUD line, result card, input gate, run
snapshot/restore, demo flag, 165 headless tests, ruff clean, and an offscreen Ursina probe of the
whole loop. Shipped behaviour is in [`docs/gui/gui-scaffold.md`](docs/gui/gui-scaffold.md) and the
integration contract in [`docs/gui/solver-integration.md`](docs/gui/solver-integration.md).

## Next

- [ ] Land `bloxorz.solvers` (#18–#23): `bfs`, `dfs`, `ucs`, `astar`, each
      `solve(stage, caps) -> SearchResult` with the frozen loop shape, plus the
      `ALGORITHMS = {"BFS": …, "DFS": …, "UCS": …, "A*": …}` mapping.
- [ ] Inject it in `Source/main.py`: `run(args.stage, solve=ALGORITHMS)`; then delete
      `Source/bloxorz/gui/demo_solver.py` and the `--replay-demo` flag.
- [ ] Re-run the offscreen probe with four cards, including a split stage (L4-01).
- [ ] Benchmarks: `PYTHONPATH=Source python -m bloxorz.bench.run_all` → `Report/data`, tables,
      figures.
- [ ] Update docs for the real solvers: drop the demo-flag notes from `README.md`,
      `AGENTS.md` and `docs/gui/gui-scaffold.md`.
- [ ] Submission: add `Report.pdf`, run `python tools/verify_submission.py .`, commit clean.

## GUI limitations that stay (accepted)

- Level select shows stage ids only and has no route back to the title screen.
- Split, merge and teleport transitions snap instead of rolling — forward, on undo, during a movie.
- The solver card shows `Counts` only; time/memory belong to the bench harness (contract rule 5).
- Playback restarts the level and restores the player's run on stop or close.
- The Solve panel exists only when a mapping is injected.
