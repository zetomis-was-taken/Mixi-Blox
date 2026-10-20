# Credits and stage provenance

Bloxorz is a 3D block puzzle by Damien Clarke, published in 2007. The stages here were transcribed
from the Coolmath Games build: <https://www.coolmathgames.com/0-bloxorz>, accessed 2026-10-20.

Course policy allows that reuse. Project 1 FAQ, accessed 2026-10-20:

- **Q1**, ready-made test cases: *"Được em."* (yes)
- **Q2 and Q9**, how many stages: *"Tối thiểu 10 em nhé."* (at least 10)
- **Q5 and Q12**, existing source or assets: *"Được (nhớ cite đầy đủ nhé)."* (yes, cite fully)

This file is that citation. No further licence is claimed: the layouts remain their author's work and
appear here only for coursework. Original stages carry `"source": "original"` and need no attribution
beyond this line.

## The benchmark set

| ID | Name | Group | Origin | Cited source | Checked |
| --- | --- | --- | --- | --- | --- |
| `FIX-01` | Straight line | L1 | original | authored for the engine tests (#38) | loads, solvable in 6 |
| `FIX-02` | East then south | L1 | original | authored for the engine tests (#38) | loads, solvable in 4 |
| `FIX-03` | South then east | L1 | original | authored for the engine tests (#38) | loads, solvable in 4 |
| `L1-01` | Plain Intro | L1 | transcribed | Coolmath Games, Bloxorz, level 1 (passcode 780464) | matches the reference exactly; solvable in 7 |
| `L4-01` | Split into the far room | L4 | transcribed | Coolmath Games, Bloxorz, level 8 (passcode 499707) | matches the reference exactly; solvable in 10 |
| `L1-02` | Turning Corner | L1 | claimed transcription, unsourced | cites stage 2 | **does not match any original level** |
| `L1-03` | Narrow Corridors | L1 | claimed transcription, unsourced | cites stage 4 | **does not match any original level** |
| `L2-01` | Fragile Crossing | L2 | claimed transcription, unsourced | cites "Fragile Bridge" | **does not match any original level** |
| `L2-02` | Fragile Stepping Stones | L2 | claimed transcription, unsourced | cites "Fragile Stepping" | **does not match any original level** |
| `L2-03` | Fragile Maze | L2 | claimed transcription, unsourced | cites stage 6 | **does not match any original level** |

Ten stages: three hand-solved `FIX` fixtures, one verified transcription, and six from #25 of which
five are unsourced. `FIX-01` to `FIX-03` and `L4-01` are on `main`; the rest arrive with #25 or
replace it.

## The provenance audit

The original levels were extracted from the game's SWF and published as text in
`jacobcoughenour/bloxorz_gba`, `game/levels.json`: 33 levels keyed by the game's own passcodes, one
letter per mechanic (`b` floor, `e` exit, `f` fragile, `s` soft switch, `h` heavy switch, `k`/`l`/`q`/`r`
bridge halves, `v` split). That file also settles whether a claim of transcription is true.

**One of the six holds up.** `L1-01` reproduces original level 1 exactly: same 6x10 bounding box, same
35 cells, same walls, same exit, same spawn, after mapping letters to glyphs.

**The other five match no level in the set**, at any size. They are playable boards with invented
citations, and they are marked unsourced above rather than attributed to stages they do not reproduce.
Two of them also disagree with their own names: `L1-03` is "Stage 03" and cites stage 4, and `L2-01`
and `L2-02` name no number at all.

Until those five are replaced with real transcriptions or re-labelled as original boards, the report
may not cite a Coolmath stage for them.

## What "checked" means, and what it does not

Solvability was measured with a breadth-first search over the engine, used as verification only. No
`expected.optimal_cost` in the repository came from a solver: the fixtures' costs were derived by hand
and the solver run only confirms the boards are finishable.

A transcribed stage comes out of `tools/transcribe_levels.py`, which only rewrites data and cannot
alter a board. Each one is then diffed against the reference and solved, in that order.

**Board fidelity is checked mechanically, where a stage claims to be a transcription.** The extracted
level data above is the reference, and the comparison is exact: same bounding box, same cells, same
spawn, same exit. Five claims fail that check. Nothing in the table says "identical to stage N" unless
the comparison passed.

## Not in the set

Six transcribed boards from #25 are unsolvable and are excluded:

| Stage | Result |
| --- | --- |
| `L3-01` soft_switch_bridge | unsolvable, 4 nodes: the start is in a pocket |
| `L3-02` heavy_switch_logic | unsolvable, 29 nodes |
| `L3-03` dual_switch_coordination | does not load; 74 nodes and still unsolvable once it does |
| `L4-01` combined_fragile_and_switches | unsolvable, 58 nodes |
| `L4-02` split_switch_intro | unsolvable, 50 nodes |
| `L4-03` split_remote_coordination | unsolvable, 96 nodes |

Every one strands the block within two moves of the start, so this is transcription rather than
mechanics. They are being replaced, not repaired, and the L3 and L4 groups are therefore empty until
that work lands. A stage measured as `UNSOLVABLE` for all four algorithms would read as a result about
the algorithms, which is the one mistake this benchmark cannot afford.

## Adding a stage

1. Write the file under `Source/bloxorz/core/stages/`, keys from the frozen schema only.
2. Load it with `load_stage`. A `StageError` means the file, not the engine.
3. Confirm it is solvable before committing it. An unsolvable board is not a hard benchmark, it is a
   missing corridor.
4. Give it a unique `id`, a `group`, and either `"source": "original"` or an entry in the table above.
