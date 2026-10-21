# BinElvan3126: informed search handoff

## Final verification and publication scope

On 2026-10-21 the user explicitly authorized completion, commits and pushing this feature branch.
This supersedes the earlier local-only restriction for this task. PR/issue/comment changes,
remote PR merges, deletion of existing work and destructive Git operations remain excluded.
PR text below is a suggestion for the human user; no PR is created or modified automatically.

The newly prepared #29 contribution is `Report/sections/informed_search.tex`, plus the scoped
AI-use appendix in `Report/sections/informed_search_ai_usage.tex`. The insertion instructions
and surrounding-template findings are in `Report/sections/informed_search_integration.md`.
The existing report main document and teammates' implementation files are untouched.

Per-issue acceptance, dependencies and verification are tracked in
`docs/informed_search_task_checklist.md`. Upstream `0f782dd` (PR #59), which requires an explicit
initial state in every bridge entry, was merged into this branch without conflicts in `1462fcd`.
The integrated feature checkout passes **139 tests**, Ruff lint and the scoped formatting check.
No frozen signature was changed by the report contribution.

The two assigned `.tex` sources compiled successfully in the isolated preview project
`output/latex/informed-search-review-20261021/` using the desktop editor's compiler. The first
attempt timed out; the retry succeeded. This verifies these fragments with the required packages,
not the entire unmerged report template or its surrounding content. The original template's
orientation-penalty claim was checked against a reachable one-move goal state and overestimates.

Commit subject for the report contribution:
`Add Vietnamese LaTeX sections for informed search`.

Suggested addition to a future PR description (do not post automatically):

> Supply insertable Vietnamese UCS/A* report sections matching the open #25 template's
> subsection structure, including the implemented non-uniform cost, c_min proof, Manhattan/2
> heuristic, teleport fallback, correctness evidence and scoped AI-use disclosure. Preserve
> the report owner's main document and list the template discrepancies needing owner review.
> Verify the existing solver contribution against latest main, including PR #59's strict
> bridge schema. No benchmark measurements or BFS/DFS modules added.
>
> Refs #29 (assigned sections only); Refs #18 (shared-loop contribution awaiting owner review).

## Branch handoff

Branch: `feat/informed-search`, including main at `0f782dd`.
The changes cover #7, #22, #23, the reusable-loop contribution to shared issue #18, and the
assigned Vietnamese report sections under #29. Commits use the repository's configured
BinElvan3126 author identity. The authorized publication target is this feature branch;
the remote SHA is verified after pushing and reported in the final handoff.

For review, open a PR into `main` using the description below. FIFO/LIFO remain shared-loop extension
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

Validation: 139 pytest tests, Ruff lint and scoped formatting checks pass. The Vietnamese
LaTeX fragments compile in an isolated preview. Tests compare UCS/A*
against independent exact weighted remaining costs over all 2,946 reachable states of ten
official stages, replay returned paths, and cover weighted route tradeoffs, reopening, stale
entries, caps, invalid costs, the shared FIFO/LIFO extension points and the UCS/A* CLI.

Integration notes: the cap wording now distinguishes time-before-pop from node-cap-after-goal,
matching the existing contract pseudocode. No frozen signature changes. Benchmark harness,
charts, separate BFS/DFS solvers and full-team performance analysis are outside this branch.
The assigned report fragments are insertable inputs; the report owner retains responsibility
for inserting them into the unmerged #25 template and reviewing surrounding inconsistencies.

Closes #7

Closes #22

Closes #23

Refs #18

Refs #29 (assigned sections only)

## Oral-exam preparation

Be able to explain why weighted UCS can return more moves, why discovery-on-push differs from
cheaper-path reinsertion, how canonical cube indices are replayed, why Manhattan/2 fails with
teleportation, the c_min admissibility/consistency argument, and both cap orderings.
The report discloses Codex assistance and the verification used.
