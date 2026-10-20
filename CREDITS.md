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

| ID | Name | Group | Level | Checked |
| --- | --- | --- | --- | --- |
| `L1-01` | Long corridor | L1 | level 1, passcode 780464 | solvable in 7 |
| `L1-02` | Two flights | L1 | level 3, passcode 918660 | solvable in 22 |
| `L1-03` | Side rooms | L1 | level 6, passcode 524383 | solvable in 35 |
| `L2-01` | Fragile shelves | L2 | level 4, passcode 520967 | solvable in 28 |
| `L2-02` | Fragile ring | L2 | level 13, passcode 448106 | solvable in 46 |
| `L3-01` | Bridge under a heavy switch | L3 | level 7, passcode 189493 | solvable in 44 |
| `L3-02` | A one-way bridge | L3 | level 11, passcode 291709 | solvable in 47 |
| `L3-03` | Two heavy switches | L3 | level 12, passcode 958640 | solvable in 65 |
| `L4-01` | Split into the far room | L4 | level 8, passcode 499707 | solvable in 10 |
| `L4-02` | Split across the middle | L4 | level 9, passcode 74355 | solvable in 24 |

Ten stages, one file each, all transcribed from the original game and all checked: every one loads,
every one is solvable, and every one matches the reference level cell for cell. The four groups are
the ladder § Stage names, so the report prints one table per group.

Three hand-authored boards live in `tests/fixtures/`, not here. They are inputs for the engine tests,
they are six moves long, and counting them as benchmark stages would pad the L1 row with puzzles that
prove nothing.

## The provenance audit

The original levels were extracted from the game's SWF and published as text in
`jacobcoughenour/bloxorz_gba`, `game/levels.json`: 33 levels keyed by the game's own passcodes, one
letter per mechanic (`b` floor, `e` exit, `f` fragile, `s` soft switch, `h` heavy switch, `k`/`l`/`q`/`r`
bridge halves, `v` split). That file also settles whether a claim of transcription is true.

**One of the six held up.** `L1-01` reproduced original level 1 exactly. The other five matched no
level in the set, at any size: playable boards carrying invented citations. Two also disagreed with
their own names, `L1-03` being "Stage 03" while citing stage 4.

They are not repaired but replaced. The ten stages in the table are transcribed straight from the
reference, so a claim of transcription is now the default rather than the exception, and
`tools/transcribe_levels.py` regenerates every one of them: run it and diff the output, and any
disagreement means the file or the tool is wrong, never the level.

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

## What is not in the set

The twelve boards that arrived in #25 are gone rather than repaired. Six of them stranded the block
within two moves of the start; of the other six, one reproduced level 1 and five matched no level at
all. All twelve were re-transcribed from the reference. Their ids are reused here: #25 must delete its stage files when it merges instead
of leaving them to collide, and `test_stage_ids_are_unique` fails if both land.

An unsolvable board is the one mistake this benchmark cannot afford: measured as `UNSOLVABLE` for all
four algorithms, it would read as a result about the algorithms. That is why
`test_every_committed_stage_loads` exists, and why a board that cannot load is not committed at all.

## Adding a stage

1. For a real level, run `tools/transcribe_levels.py` rather than typing a grid: it writes the file,
   and it refuses to write one that disagrees with the reference.
2. Load it with `load_stage`. A `StageError` means the file, not the engine.
3. Confirm it is solvable before committing it, and put the number in the table above.
4. Give it a unique `id`, a `group` from the ladder, and either `"source": "original"` or a row here.
