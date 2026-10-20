"""Transcribe original Bloxorz levels into the frozen stage schema.

The reference is `game/levels.json` from jacobcoughenour/bloxorz_gba, which carries the 33 levels
extracted from the game's SWF, keyed by the game's own passcodes. Its format, as read from that
project's asset tool:

    tiles     one letter per cell: b floor, e exit, f fragile, s soft switch, h heavy switch,
              v split, k/l bridge-left on/off, q/r bridge-right on/off, space void
    spawn     [x, y] of the standing block
    switches  {"x*10+y": [[bridge_x, bridge_y, mode], ...]}  mode: onoff, on, off
    splits    {"x*10+y": [x1, y1, x2, y2]}                    where the two cubes land

This script only rewrites data. It does not import the engine, so it cannot turn a bad board into a
good one; load and solve the result to prove it is playable.
"""

from __future__ import annotations

import json
from pathlib import Path

GLYPH = {
    " ": ".",
    "b": "o",
    "e": "G",
    "f": "f",
    "s": "+",
    "h": "X",
    "v": "Y",
    "k": "=",
    "l": "=",
    "q": "=",
    "r": "=",
}
BRIDGE_OPEN = {"k": True, "q": True, "l": False, "r": False}
SWITCH_TYPE = {"s": "soft", "h": "heavy"}
# The reference has three modes. `toggle` maps straight across; `on` and `off` are one-way.
MODE = {"onoff": "toggle", "on": "on", "off": "off"}

PLAN: dict[int, tuple[str, str, str]] = {
    7: ("L3-01", "Bridge under a heavy switch", "L3"),
    8: ("L4-01", "Split into the far room", "L4"),
}


def to_cell(key: str) -> tuple[int, int]:
    """The reference keys a cell as x*10+y, with ten rows. Returns (row, col)."""
    value = int(key)
    return (value % 10, value // 10)


def transcribe(level: dict, stage_id: str, name: str, group: str) -> dict:
    tiles = level["tiles"]
    spawn_x, spawn_y = level["spawn"]
    switches = level.get("switches") or {}
    splits = level.get("splits") or {}

    grid: dict[tuple[int, int], str] = {}
    for y, row in enumerate(tiles):
        for x, ch in enumerate(row):
            if ch != " ":
                grid[(y, x)] = GLYPH[ch]

    grid[(spawn_y, spawn_x)] = "S"

    bridges = []
    for y, row in enumerate(tiles):
        for x, ch in enumerate(row):
            if ch in BRIDGE_OPEN:
                bridges.append({"pos": [y, x], "initially_open": BRIDGE_OPEN[ch]})

    entries = []
    for key, links in switches.items():
        y, x = to_cell(key)
        ch = tiles[y][x]
        for bridge_x, bridge_y, mode in links:
            entries.append(
                {
                    "type": SWITCH_TYPE[ch],
                    "pos": [y, x],
                    "action": MODE[mode],
                    "bridges": None,
                    "teleport_cubes": None,
                    "_bridge": [bridge_y, bridge_x],
                }
            )

    merged: dict[tuple[int, int], dict] = {}
    for entry in entries:
        cell = tuple(entry["pos"])
        if cell not in merged:
            merged[cell] = entry
            merged[cell]["bridges"] = []
        merged[cell]["bridges"].append(entry.pop("_bridge"))

    for key, targets in splits.items():
        y, x = to_cell(key)
        x1, y1, x2, y2 = targets
        merged[(y, x)] = {
            "type": "split",
            "pos": [y, x],
            "action": None,
            "bridges": None,
            "teleport_cubes": [[y1, x1], [y2, x2]],
        }

    # Emit the reference grid whole, leading void included: every coordinate below then matches the
    # source data, which makes the fidelity check a straight diff and keeps switch positions honest.
    width = max(len(row) for row in tiles)
    rows = ["".join(grid.get((y, x), ".") for x in range(width)) for y in range(len(tiles))]

    stage = {
        "id": stage_id,
        "name": name,
        "group": group,
        "source": f"Coolmath Games, Bloxorz, level {level['_number']} (passcode {level['code']})",
        "grid": rows,
        "switches": [merged[cell] for cell in sorted(merged)],
        "bridges": bridges,
    }
    return stage


def verify(stage: dict, level: dict) -> list[str]:
    """Compare a stage with the reference, cell by cell, before it is written.

    This catches offsets, cropping and stale files, which is where the first version of this tool
    went wrong. It cannot catch a misreading of the reference, because both sides use the same map.
    """
    tiles = level["tiles"]
    width = max(len(row) for row in tiles)
    spawn = (level["spawn"][1], level["spawn"][0])
    problems: list[str] = []
    for y in range(len(tiles)):
        written = stage["grid"][y] if y < len(stage["grid"]) else ""
        for x in range(width):
            want = "S" if (y, x) == spawn else GLYPH[tiles[y][x] if x < len(tiles[y]) else " "]
            got = written[x] if x < len(written) else ""
            if want != got:
                problems.append(f"({y},{x}): wrote {got!r}, reference says {want!r}")
    return problems


def main(reference: Path, out: Path, numbers: list[int]) -> None:
    levels = json.loads(reference.read_text(encoding="utf-8"))["levels"]
    for number in numbers:
        stage_id, name, group = PLAN[number]
        level = dict(levels[number - 1], _number=number)
        stage = transcribe(level, stage_id, name, group)
        problems = verify(stage, level)
        if problems:
            first = problems[0]
            raise SystemExit(f"level {number}: {len(problems)} cells disagree, first: {first}")
        slug = name.lower().replace(" ", "_")
        path = out / f"{stage_id}_{slug}.json"
        path.write_text(json.dumps(stage, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"level {number:>2} -> {path.name}")


if __name__ == "__main__":
    import sys

    main(Path(sys.argv[1]), Path(sys.argv[2]), [int(arg) for arg in sys.argv[3:]])
