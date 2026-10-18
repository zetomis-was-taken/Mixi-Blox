# ADR-001: Write the report in Vietnamese

## Status

Accepted

## Date

2026-10-18

## Context

The report is a formatted PDF (§3.6), and FAQ Q3 permits English or Vietnamese but forbids mixing the two within one report. The language has to be fixed before drafting starts, because the §3.5 heuristic argument and every figure caption, table header and appendix entry is written against it.

The issue proposed English, since the course, the project PDF and the algorithm vocabulary (admissibility, consistency, frontier) are English. The team decided against that proposal.

## Decision

The report is written in Vietnamese throughout, chosen by **aFlyingSeal** and **Alexvuong2006** for native fluency: the argument is faster to write and stronger to defend in the language the team thinks in.

The rule covers the whole report — body, figure captions, table headers and appendix. Code, comments, commit messages and engineering docs under `docs/` stay English; only the report is Vietnamese.

## Alternatives Considered

### English

- Pros: matches the course, the project PDF and the algorithm vocabulary; §3.5 gets written once instead of translated; no risk of an inconsistent Vietnamese terminology.
- Cons: the team writes and argues in Vietnamese; drafting in a second language costs time on a 15-day schedule and flattens the prose.
- Rejected: native fluency outweighed vocabulary reuse.

## Consequences

- Algorithm terms are used in Vietnamese with the English term in parentheses on first use, e.g. "tính khả dụng (admissibility)".
- Captions, table headers and the appendix follow the same rule — a single English section violates Q3.
- English source material (textbook definitions, the project PDF) must be translated, or quoted and clearly framed as a quotation.
