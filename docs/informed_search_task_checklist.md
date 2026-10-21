# Local engineering checklist: BinElvan3126

## Session rules

- [x] Read the workspace AGENTS.md and preserve it; no replacement instructions created.
- [x] Inspect the working tree, history, README, contract, relevant issues/comments and PR reviews.
- [x] Apply the latest user authorization: complete, commit and push `feat/informed-search` for this task.
- [x] Keep PR/issue/comment changes and remote PR merges outside this authorization.
- [x] Preserve existing files and teammate changes; do not delete work or use destructive Git operations.
- [x] Keep #19/#20/#24 implementations and benchmark/chart generation outside this branch.
- [x] Review the final diff and prepare only the scoped contribution for commit and push.

## Team and upstream snapshot

Current branch: `feat/informed-search`; starting implementation HEAD: `ae5ace3`.
The report preparation began with a clean tree. After the user's explicit publishing authorization,
upstream `0f782dd` was merged without conflicts in `1462fcd`. The integrated branch passes 139 tests.

| Workstream | Owner / authority | Observed state |
| --- | --- | --- |
| Core, transitions, stage loading, State/Action clauses | TanKhoiTV; aFlyingSeal for schema decisions | Core merged; PR #59 additionally requires explicit bridge initial state |
| #18 shared loop and #31 solver return API | aFlyingSeal | #18 open; local reusable-loop contribution exists and awaits owner review |
| #7, #22, #23 | BinElvan3126 | Open on GitHub; implementations and tests verified for branch publication |
| #29 Vietnamese report coordination | aFlyingSeal | Open; this session supplies only assigned UCS/A*/cost sections |
| #24, infrastructure and LaTeX template | Alexvuong2006 | PR #25 `7ae7650` remains open; latest revision includes the requested rebase and legacy-result-branch removal; owner approval still pending |
| GUI and demo | zetomis-was-taken | Separate workstream; not modified here |

`CONTRIBUTING.md` is absent from this checkout and current main; contributing rules are in README
and `docs/contracts.md`. Do not infer that the old closed, unmerged CONTRIBUTING PR is active policy.

## Dependency order and acceptance evidence

| Issue | Requirements / acceptance criteria | Existing evidence | Safe remaining work / dependencies |
| --- | --- | --- | --- |
| #7 | Defined positive minimum; same cost model and heuristic scale; written argument | `core/costs.py`, cost-policy tests, report section 2, A* heuristic | Recheck against latest merged core; no standalone control-switch edge under frozen Action |
| #18 (contribution) | One loop, canonical keys, counts, caps, O(1) Board construction, frozen result API | `solvers/base.py`, FIFO/LIFO strategy tests, goal/cap/stale-entry tests | Validate without changing aFlyingSeal's frozen API; owner review still needed |
| #22 | Heap ordered by g, non-uniform policy outside loop, path cost vs length, weight rationale | UCS adapter, weighted route and independent oracle tests | Include actual policy and reasoning in assigned LaTeX section |
| #23 | g+h, admissible/consistent heuristic under actual costs, tiny-stage exact-cost test, reopen improvements | A* adapter; tiny fixtures, ten-stage reverse oracle and inconsistent-heuristic reopening test | Include proof and split/teleport limitation in LaTeX; verify agreement on latest main |
| #29 (assigned sections) | Vietnamese prose/captions/headers/appendix; first-use English terms in parentheses; existing LaTeX structure | Vietnamese Markdown exists; PR #25 has UCS/A* subsections | Add separate insertable `.tex` sections, validate compilation, preserve teammates' main.tex |

## Working plan

1. [x] Audit the current team decisions and open PR state before editing.
2. [x] Prepare UCS/A* LaTeX replacement subsections and a scoped AI-use appendix.
3. [x] Compile the assigned sections in an isolated local preview. First attempt timed out without
   source diagnostics; the bounded retry succeeded with the desktop editor's compiler.
4. [x] Test the feature contribution against current main in a separate local checkout: 139 passed.
5. [x] Rerun tests/lint and review compatibility/duplicate-definition gates: integrated feature 139 passed;
   Ruff lint and scoped formatting clean. Relative report links/labels checked.
6. [x] Record per-issue status, changed files, limitations, integration notes and suggested commit/PR text.

## Integration risks to report, not silently fix

- PR #25 is unmerged. Its report template still documents different weights, a separate control-change
  action, an unsupported orientation penalty and unmeasured performance claims. Only the assigned
  subsections will be supplied as replacement inputs; other report sections need their owners' review.
- The latest #25 revision includes the rebase and removal requested by the last review. It is still
  unmerged; do not claim approval or modify that teammate's harness. No measurements are manufactured.
- Main's PR #59 is integrated and its strict bridge-schema regression test passes.
- Existing feature commits change the core cost hook and clarify contract cap wording. These are
  pre-existing changes; this session will not extend frozen clauses or engine ownership without review.
- No new benchmark numbers will be produced. The L2-02 cost/move example is a correctness test,
  not a timing/memory experiment. The full #29 issue and #18 ownership are not claimed complete.

## Per-issue local handoff

All issues remain open remotely. "Verified" below means local acceptance evidence, not merged,
approved or automatically closed. No new solver defect was found by this audit; the safe missing
deliverable was the assigned LaTeX report content, so implementation focused there.

| Issue / contribution status | Implementation and files | Verification | Limitations and dependencies | Suggested per-issue commit subject |
| --- | --- | --- | --- | --- |
| #7: existing implementation verified | `core/costs.py`, `Board.step_cost`; c_min=1 and contact-based policy; new LaTeX cost subsection | Cost tests including stationary cubes/teleports and all reachable-edge lower bounds; full suites | Older issue text mentions paid cube switching; frozen Action has no such edge. Existing core hook/contract wording needs owner review | `Define the minimum action cost and fragile contact policy` |
| #18: contribution verified, owner integration pending | Existing `solvers/base.py`; new report explains FIFO/LIFO/heap, caps and Counts | Strategy tests, exact node cap, zero/expired time cap, cycles, stale entries and reopening; contract gates | aFlyingSeal owns the issue/API. No standalone BFS/DFS modules or benchmark harness added | `Provide shared search bookkeeping and cap hooks` |
| #22: existing implementation verified | Existing `solvers/ucs.py` and shared loop; new UCS LaTeX subsection | Hand-solved fixtures, independent weighted reverse oracle, L2-02 longer/cheaper path, CLI | Optimizes cost, not moves; full experiments wait for #24 and final integration | `Implement uniform-cost search over the shared cost policy` |
| #23: existing implementation verified | Existing `solvers/astar.py`; new heuristic/admissibility/consistency LaTeX subsections | Tiny-stage remaining-cost bounds, every edge on ten stages, UCS agreement, inconsistent-heuristic reopening | On split stages h=0; no claimed speedup or unproved orientation penalty | `Implement A star with a cost-aware admissible heuristic` |
| #29: assigned sources compiled, owner insertion pending | `Report/sections/informed_search.tex`, `informed_search_ai_usage.tex`, integration notes; links in README/Markdown | Vietnamese prose and first-use terminology reviewed; labels/links checked; isolated preview compilation succeeded on retry | PR #25 remains open; report owner must insert sections and review surrounding contradictions. Whole report issue remains open | `Add Vietnamese LaTeX sections for informed search` |

The shared suggested PR description is in `docs/informed_search_handoff.md`. It references #18
and the assigned #29 contribution rather than claiming completion of the other owners' work.

## Final session checks

- Feature includes the normal upstream merge `1462fcd`; no rebase or force push is used.
- The report contribution edits only owned report/checklist/handoff documentation and README links.
  All new files in `Report/` are the two assigned source fragments and their integration notes.
- The standalone preview is outside the repository at
  `output/latex/informed-search-review-20261021/`; it does not replace the group report.
- The orientation-penalty counterexample was also checked against FIX-01: a reachable lying
  state has `h=0.5` and one legal goal move costing 1, so adding 1 would overestimate at 1.5.
- No timing/memory measurements or performance claims were added. No existing teammate report
  content or original AGENTS.md was replaced. The only core/schema updates in this finalization
  are the already approved upstream changes from PR #59.
