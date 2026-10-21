# Integration of the assigned Vietnamese report sections (#29)

Reference: the existing LaTeX structure in open PR #25 at `7ae7650`, checked on 2026-10-21. It is a reference,
not a merged main document. These files add only BinElvan3126's assigned content and
do not copy, replace or edit the other members' `Report/main.tex`.

## Insertion points for the report owner

1. In the existing algorithm section, replace the two old UCS and A* subsections
   (from `\subsection{Uniform-Cost Search (UCS)}` through the A* subsection, before
   the next experimental-setup section) with:

   ```tex
   \input{sections/informed_search}
   ```

2. Within the existing AI-use appendix, insert the assigned disclosure:

   ```tex
   \input{sections/informed_search_ai_usage}
   ```

3. Compile the integrated report using its existing preamble. These fragments use
   `amsmath` and `hyperref` (`\path`), already present in the referenced template.
   The isolated preview additionally uses T5 font encoding for Vietnamese under pdfLaTeX.

The isolated project at `output/latex/informed-search-review-20261021/` compiled successfully
with the desktop editor's compiler. Its source inputs are copies of these exact two fragments.
This does not certify compilation of the surrounding, unmerged group template.

Do not append the new content while leaving the old UCS/A* subsections in place: that
would leave contradictory weights and two different heuristics in the same report.

## Findings for the owners of the surrounding sections

- The reference template's 1/3/1.5/2 cost table does not describe the actual implementation.
  The assigned fragment states the implemented contact-based cost and its minimum.
- Its orientation penalty is not implemented and is unsafe as written; the fragment gives
  the actual heuristic, the teleport fallback and a one-step counterexample to that penalty.
- The surrounding problem-formalization section still describes `SwitchControl` and a
  three-component state key. The frozen API uses a cube-indexed movement action and the
  two-field `State(cubes, bridges)`. Those sections belong to their owners and are untouched.
- The surrounding results discussion still asserts an unmeasured 40–70% reduction and says
  A* always minimizes move count. Neither claim follows from this weighted implementation.
  Actual measurements and owner review are required before those paragraphs can be final.
- The GUI section describes Pygame while ADR-002 selected Ursina. This is a separate owner check.

This contribution contains proofs and correctness checks only. Benchmark tooling, charts and
standalone BFS/DFS implementations remain excluded as requested. Completion of these fragments
does not close the whole #29 report issue, which remains under aFlyingSeal's coordination.
