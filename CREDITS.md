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
| `L1-01` | Plain Intro | L1 | transcribed | Coolmath Games, Bloxorz, stage 1 (passcode 780464) | loads, solvable in 7 |
| `L1-02` | Turning Corner | L1 | transcribed | Coolmath Games, Bloxorz, stage 2 | loads, solvable in 14 |
| `L1-03` | Narrow Corridors | L1 | transcribed | Coolmath Games, Bloxorz, stage 4 | loads, solvable in 10 |
| `L2-01` | Fragile Crossing | L2 | transcribed | Coolmath Games, Bloxorz, "Fragile Bridge" | loads, solvable in 9 |
| `L2-02` | Fragile Stepping Stones | L2 | transcribed | Coolmath Games, Bloxorz, "Fragile Stepping" | loads, solvable in 16 |
| `L2-03` | Fragile Maze | L2 | transcribed | Coolmath Games, Bloxorz, stage 6 | loads, solvable in 11 |

Nine stages, four of them hand-solved fixtures and five transcribed. **Six of these arrive with
#25**; the three `FIX` stages are already on `main`.

Two entries need their citation tightened before the report names them:

- `L1-03` is named "Stage 03" and cites **stage 4**. One of the two is wrong.
- `L2-01` and `L2-02` cite descriptive names rather than stage numbers, so the report cannot say which
  level they came from.

## What "checked" means, and what it does not

Solvability was measured with a breadth-first search over the engine, used as verification only. No
`expected.optimal_cost` in the repository came from a solver: the fixtures' costs were derived by hand
and the solver run only confirms the boards are finishable.

**Board fidelity to the original game was not verified.** Transcribing a level from play and checking
it against a reference are different claims. The reference was unavailable: the open-source Bloxorz
clones carry their own small demo boards rather than the 33-stage set, so comparing against them would
prove nothing. Until someone plays the level beside the JSON, the table above claims "transcribed from
the Coolmath build", not "identical to stage N".

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
