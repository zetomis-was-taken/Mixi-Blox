# BinElvan3126: informed search handoff

## Ready to upload

Branch: `feat/issue-22-23-informed-search`, based on the latest main fetched during this task.
The changes cover #7, #22, #23 and the reusable-loop contribution to shared issue #18.
The local commit uses the repository's configured BinElvan3126 author identity. Nothing has
been pushed and no issue/PR has been modified remotely.

From the repository root:

```powershell
git status --short
git log -1 --oneline
git push -u origin feat/issue-22-23-informed-search
```

Then open a PR into `main` using the description below. Coordinate adoption of the FIFO/LIFO
adapters with the #19/#20 owner. This handoff does not claim that person's allocated work,
the GUI/video, or the full-team harness/report. Shared issue #18 is referenced rather than
automatically closed so its co-owner can review the integration.

## Verify locally

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m Source.main --stage Source/bloxorz/core/stages/L2-02_fragile_ring.json --solver ucs
$env:PYTHONPATH = 'Source'
python -m bloxorz.bench.informed_search --markdown docs/informed_search_results_vi.md
```

The report section is `docs/report_ucs_astar_vi.md`; the complete measured table is
`docs/informed_search_results_vi.md`. Raw JSON/CSV and PNG/SVG figures are ignored, available
locally under `Report/data/informed_search/` and `Report/figures/informed_search/`, and fully
regenerable. No generated solver output or environment/cache is included in the commit.

## Proposed PR title

Implement weighted UCS and A* with a shared search loop

## Proposed PR description

UCS now minimizes a concrete non-uniform cost: one roll plus one per newly contacted fragile
tile. On L2-02, BFS returns 46 moves/cost 64, while UCS/A* choose 49 moves/cost 58. Weights live
outside the transition rules; control selection creates no separate charged action.

The shared #18 loop owns caps, counters, canonical-key duplicate handling and parent paths.
FIFO/LIFO adapters exercise BFS/DFS integration, while UCS/A* use a heap with cheaper-path
reinsertion and stale-entry rejection. A* uses occupied-cell Manhattan/2 and a safe zero
fallback on split/teleport stages, with admissibility/consistency arguments in the Vietnamese
report. The CLI now invokes actual solvers and returns JSON results.

Validation: the full pytest suite, Ruff lint and formatting checks pass. Tests compare UCS/A*
against independent exact weighted remaining costs over all 2,946 reachable states of ten
official stages, replay every solver's paths, and cover weighted route tradeoffs, reopening,
stale entries, caps, invalid costs, measurement cleanup/medians and CLI behavior. The isolated
measurement tool completes 40 algorithm-stage pairs, three repetitions each, and exports raw
samples, a measured Vietnamese table and five comparison charts.

Integration notes: the cap wording now distinguishes time-before-pop from node-cap-after-goal,
matching the existing contract pseudocode. No frozen signature changes. The separate measurement
module does not replace the #24 harness. The final group report should rerun the shared harness
after final BFS/DFS and GUI integration. Coordinate the thin FIFO/LIFO adapters with their owners.

Closes #7

Closes #22

Closes #23

Refs #18

## Oral-exam preparation

Be able to explain why weighted UCS can return more moves, why discovery-on-push differs from
cheaper-path reinsertion, how canonical cube indices are replayed, why Manhattan/2 fails with
teleportation, the c_min admissibility/consistency argument, both cap orderings, and why heap
peak is not whole-process RAM. The report discloses Codex assistance and the verification used.
