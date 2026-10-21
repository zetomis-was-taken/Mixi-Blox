# BinElvan3126: informed search handoff

## Ready to upload

Branch: `feat/informed-search`, based on the latest main fetched during this task.
The changes cover #7, #22, #23 and the reusable-loop contribution to shared issue #18.
The local commit uses the repository's configured BinElvan3126 author identity. Nothing has
been pushed and no issue/PR has been modified remotely.

From the repository root:

```powershell
git status --short
git log -1 --oneline
git push -u origin feat/informed-search
```

Then open a PR into `main` using the description below. FIFO/LIFO remain shared-loop extension
points under #18; the separate BFS/DFS solvers and all benchmark/chart work have been removed.
The #18 owner, aFlyingSeal, should review that integration. This PR does not automatically close
their issue or claim the GUI/video and full-team experiments work.

## Verify locally

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
```

The Vietnamese report section is `docs/report_ucs_astar_vi.md`. It contains cost and heuristic
arguments, shared-loop semantics and correctness evidence; it has no premature performance
tables or plots. The former full implementation is preserved on local branch
`backup/informed-search-full-20261021`; generated results/figures have been moved outside this
repository to the workspace's `output/archives/informed-search-full-20261021/` directory.

## Proposed PR title

Implement weighted UCS and A* with a shared search loop

## Proposed PR description

UCS now minimizes a concrete non-uniform cost: one roll plus one per newly contacted fragile
tile. On L2-02, a test-only minimum-move oracle finds 46 moves/cost 64, while UCS/A* choose 49
moves/cost 58. Weights live outside transition rules; selecting a cube is not a charged action.

The shared #18 loop owns caps, counters, canonical-key duplicate handling and parent paths.
FIFO/LIFO are extension points for later BFS/DFS integration; no separate BFS/DFS modules ship
here. UCS/A* use a heap with cheaper-path reinsertion and stale-entry rejection. A* uses
occupied-cell Manhattan/2 and a safe zero
fallback on split/teleport stages, with admissibility/consistency arguments in the Vietnamese
report. The CLI now invokes actual solvers and returns JSON results.

Validation: the full pytest suite, Ruff lint and formatting checks pass. Tests compare UCS/A*
against independent exact weighted remaining costs over all 2,946 reachable states of ten
official stages, replay returned paths, and cover weighted route tradeoffs, reopening, stale
entries, caps, invalid costs, the shared FIFO/LIFO extension points and the UCS/A* CLI.

Integration notes: the cap wording now distinguishes time-before-pop from node-cap-after-goal,
matching the existing contract pseudocode. No frozen signature changes. Benchmark harness,
charts, separate BFS/DFS solvers and full-team performance analysis are outside this branch.

Closes #7

Closes #22

Closes #23

Refs #18

## Oral-exam preparation

Be able to explain why weighted UCS can return more moves, why discovery-on-push differs from
cheaper-path reinsertion, how canonical cube indices are replayed, why Manhattan/2 fails with
teleportation, the c_min admissibility/consistency argument, and both cap orderings.
The report discloses Codex assistance and the verification used.
