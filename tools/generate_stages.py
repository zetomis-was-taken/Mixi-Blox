#!/usr/bin/env python3
"""
Test Set Generator for CSC14003 Bloxorz Project
  - L1: Basic (Plain tiles, orientation practice)
  - L2: Fragile (Orange tiles requiring distributed weight)
  - L3: Switches & Bridges (Soft and heavy switches, toggle/permanent bridges)
  - L4: Combined & Split (Complex stages with split switches and dual cube coordination)

Conforms to Interface Contract (Issue #8, PR #32):
  - Grid glyphs are the single source of truth for start ('S') and goal ('G').
  - No redundant 'start', 'goal', 'rows', 'cols' fields.
  - All switch entries carry complete fields ('action', 'bridges', 'teleport_cubes'
    with null when unused).
  - Clean filenames without special characters (Issue #8: no '&').
"""

import json
from pathlib import Path


def create_stages():
    stages_dir = Path(__file__).resolve().parent.parent / "Source" / "bloxorz" / "core" / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)

    # Remove any obsolete stage files (e.g. ones with '&')
    for old_file in stages_dir.glob("*_&_*.json"):
        old_file.unlink()
        print(f"[-] Removed obsolete file: {old_file.name}")

    stages = [
        # --- GROUP L1: BASIC ---
        {
            "id": "L1-01",
            "name": "Plain Intro",
            "group": "L1",
            "source": "Coolmath Games Bloxorz - Stage 1 (Passcode 780464)",
            "grid": [
                "ooo.......",
                "oSoooo....",
                "ooooooooo.",
                ".ooooooooo",
                ".....ooGoo",
                "......ooo.",
            ],
            "switches": [],
            "bridges": [],
        },
        {
            "id": "L1-02",
            "name": "Turning Corner",
            "group": "L1",
            "source": "Coolmath Games Bloxorz - Stage 2",
            "grid": [
                "..oooo......",
                "..oSoo......",
                "..oooo..ooGo",
                "....oo..oooo",
                "....oooooooo",
                "....oooo....",
            ],
            "switches": [],
            "bridges": [],
        },
        {
            "id": "L1-03",
            "name": "Narrow Corridors",
            "group": "L1",
            "source": "Coolmath Games Bloxorz - Stage 4",
            "grid": [
                ".ooooo......",
                ".oSooo......",
                ".ooooo.oooo.",
                "...oo..oooo.",
                "...ooooooGoo",
                "...ooooooooo",
                ".....ooooo..",
            ],
            "switches": [],
            "bridges": [],
        },
        # --- GROUP L2: FRAGILE TILES ---
        {
            "id": "L2-01",
            "name": "Fragile Crossing",
            "group": "L2",
            "source": "Coolmath Games Bloxorz - Fragile Bridge",
            "grid": [
                "..ooooffooo..",
                "..oSooffoGo..",
                "..ooooffooo..",
                "..oooo..ooo..",
                "..oooo..ooo..",
            ],
            "switches": [],
            "bridges": [],
        },
        {
            "id": "L2-02",
            "name": "Fragile Stepping Stones",
            "group": "L2",
            "source": "Coolmath Games Bloxorz - Fragile Stepping",
            "grid": [
                "..oooo........",
                "..oSooff..oooo",
                "..ooooff..oGoo",
                "......ff..oooo",
                "......ff..oooo",
                "......ffoooo..",
            ],
            "switches": [],
            "bridges": [],
        },
        {
            "id": "L2-03",
            "name": "Fragile Maze",
            "group": "L2",
            "source": "Coolmath Games Bloxorz - Stage 6",
            "grid": [
                ".ooooo......",
                ".oSooo......",
                ".oofff.oooo.",
                "..offf.ooGo.",
                "..offf.oooo.",
                "..oooo.oooo.",
                "...oooooo...",
            ],
            "switches": [],
            "bridges": [],
        },
    ]

    for s in stages:
        file_name = f"{s['id']}_{s['name'].split(' - ')[1].lower().replace(' ', '_')}.json"
        out_path = stages_dir / file_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
        print(f"[+] Created: {file_name}")

    print(f"\n[+] Successfully generated {len(stages)} stages in {stages_dir}")


if __name__ == "__main__":
    create_stages()
