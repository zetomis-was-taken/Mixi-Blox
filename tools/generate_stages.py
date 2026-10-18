#!/usr/bin/env python3
"""
Test Set Generator for CSC14003 Bloxorz Project
Generates 12 standardized test stages across 4 difficulty tiers:
  - L1: Basic (Plain tiles, orientation practice)
  - L2: Fragile (Orange tiles requiring distributed weight)
  - L3: Switches & Bridges (Soft and heavy switches, toggle/permanent bridges)
  - L4: Combined & Split (Complex stages with split switches and dual cube coordination)

Conforms to Interface Contract (Issue #8, PR #32):
  - Grid glyphs are the single source of truth for start ('S') and goal ('G').
  - No redundant 'start', 'goal', 'rows', 'cols' fields.
  - Every '=' tile is declared as an individual bridge cell.
  - All switch entries carry complete fields ('action', 'bridges', 'teleport_cubes' with null when unused).
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
            "name": "Stage 01 - Plain Intro",
            "group": "L1",
            "difficulty": "Basic",
            "source": "Coolmath Games Bloxorz - Stage 1 (Passcode 780464)",
            "grid": [
                "ooo.......",
                "oSoooo....",
                "ooooooooo.",
                ".ooooooooo",
                ".....ooGoo",
                "......ooo."
            ],
            "switches": [],
            "bridges": []
        },
        {
            "id": "L1-02",
            "name": "Stage 02 - Turning Corner",
            "group": "L1",
            "difficulty": "Basic",
            "source": "Coolmath Games Bloxorz - Stage 2",
            "grid": [
                "..oooo......",
                "..oSoo......",
                "..oooo..ooGo",
                "....oo..oooo",
                "....oooooooo",
                "....oooo...."
            ],
            "switches": [],
            "bridges": []
        },
        {
            "id": "L1-03",
            "name": "Stage 03 - Narrow Corridors",
            "group": "L1",
            "difficulty": "Basic",
            "source": "Coolmath Games Bloxorz - Stage 4",
            "grid": [
                ".ooooo......",
                ".oSooo......",
                ".ooooo.oooo.",
                "...oo..oooo.",
                "...ooooooGoo",
                "...ooooooooo",
                ".....ooooo.."
            ],
            "switches": [],
            "bridges": []
        },

        # --- GROUP L2: FRAGILE TILES ---
        {
            "id": "L2-01",
            "name": "Stage 04 - Fragile Crossing",
            "group": "L2",
            "difficulty": "Fragile",
            "source": "Coolmath Games Bloxorz - Fragile Bridge",
            "grid": [
                "..ooooffooo..",
                "..oSooffoGo..",
                "..ooooffooo..",
                "..oooo..ooo..",
                "..oooo..ooo.."
            ],
            "switches": [],
            "bridges": []
        },
        {
            "id": "L2-02",
            "name": "Stage 05 - Fragile Stepping Stones",
            "group": "L2",
            "difficulty": "Fragile",
            "source": "Coolmath Games Bloxorz - Fragile Stepping",
            "grid": [
                "..oooo........",
                "..oSooff..oooo",
                "..ooooff..oGoo",
                "......ff..oooo",
                "......ff..oooo",
                "......ffoooo.."
            ],
            "switches": [],
            "bridges": []
        },
        {
            "id": "L2-03",
            "name": "Stage 06 - Fragile Maze",
            "group": "L2",
            "difficulty": "Fragile",
            "source": "Coolmath Games Bloxorz - Stage 6",
            "grid": [
                ".ooooo......",
                ".oSooo......",
                ".oofff.oooo.",
                "..offf.ooGo.",
                "..offf.oooo.",
                "..oooo.oooo.",
                "...oooooo..."
            ],
            "switches": [],
            "bridges": []
        },

        # --- GROUP L3: SWITCHES & BRIDGES ---
        {
            "id": "L3-01",
            "name": "Stage 07 - Soft Switch Bridge",
            "group": "L3",
            "difficulty": "Switches",
            "source": "Coolmath Games Bloxorz - Stage 7",
            "grid": [
                ".ooo........o",
                ".oS+o..==..oo",
                ".ooo...==.oGo",
                ".......==.ooo",
                ".......==..oo",
                "...........oo"
            ],
            "switches": [
                {
                    "type": "soft",
                    "pos": [1, 3],
                    "action": "toggle",
                    "bridges": [
                        [1, 7], [1, 8],
                        [2, 7], [2, 8],
                        [3, 7], [3, 8],
                        [4, 7], [4, 8]
                    ],
                    "teleport_cubes": None
                }
            ],
            "bridges": [
                {"pos": [1, 7], "initially_open": False},
                {"pos": [1, 8], "initially_open": False},
                {"pos": [2, 7], "initially_open": False},
                {"pos": [2, 8], "initially_open": False},
                {"pos": [3, 7], "initially_open": False},
                {"pos": [3, 8], "initially_open": False},
                {"pos": [4, 7], "initially_open": False},
                {"pos": [4, 8], "initially_open": False}
            ]
        },
        {
            "id": "L3-02",
            "name": "Stage 08 - Heavy Switch Logic",
            "group": "L3",
            "difficulty": "Switches",
            "source": "Coolmath Games Bloxorz - Stage 8",
            "grid": [
                ".oooo........",
                ".oSoX..==....",
                ".oooo..==.ooo",
                ".......==.oGo",
                ".......==.ooo",
                "..........ooo",
                "..........ooo"
            ],
            "switches": [
                {
                    "type": "heavy",
                    "pos": [1, 4],
                    "action": "permanent",
                    "bridges": [
                        [1, 7], [1, 8],
                        [2, 7], [2, 8],
                        [3, 7], [3, 8],
                        [4, 7], [4, 8]
                    ],
                    "teleport_cubes": None
                }
            ],
            "bridges": [
                {"pos": [1, 7], "initially_open": False},
                {"pos": [1, 8], "initially_open": False},
                {"pos": [2, 7], "initially_open": False},
                {"pos": [2, 8], "initially_open": False},
                {"pos": [3, 7], "initially_open": False},
                {"pos": [3, 8], "initially_open": False},
                {"pos": [4, 7], "initially_open": False},
                {"pos": [4, 8], "initially_open": False}
            ]
        },
        {
            "id": "L3-03",
            "name": "Stage 09 - Dual Switch Coordination",
            "group": "L3",
            "difficulty": "Switches",
            "source": "Coolmath Games Bloxorz - Stage 9",
            "grid": [
                ".ooooo..==....",
                ".oSo+o..==.ooo",
                ".ooooo..==.oXo",
                "........==.ooo",
                "...........==.",
                "..........oGo.",
                "..........ooo."
            ],
            "switches": [
                {
                    "type": "soft",
                    "pos": [1, 4],
                    "action": "toggle",
                    "bridges": [
                        [0, 8], [0, 9],
                        [1, 8], [1, 9],
                        [2, 8], [2, 9],
                        [3, 8], [3, 9]
                    ],
                    "teleport_cubes": None
                },
                {
                    "type": "heavy",
                    "pos": [2, 12],
                    "action": "toggle",
                    "bridges": [
                        [4, 11], [4, 12]
                    ],
                    "teleport_cubes": None
                }
            ],
            "bridges": [
                {"pos": [0, 8], "initially_open": False},
                {"pos": [0, 9], "initially_open": False},
                {"pos": [1, 8], "initially_open": False},
                {"pos": [1, 9], "initially_open": False},
                {"pos": [2, 8], "initially_open": False},
                {"pos": [2, 9], "initially_open": False},
                {"pos": [3, 8], "initially_open": False},
                {"pos": [3, 9], "initially_open": False},
                {"pos": [4, 11], "initially_open": False},
                {"pos": [4, 12], "initially_open": False}
            ]
        },

        # --- GROUP L4: COMBINED & SPLIT BLOCKS ---
        {
            "id": "L4-01",
            "name": "Stage 10 - Combined Fragile and Switches",
            "group": "L4",
            "difficulty": "Combined",
            "source": "Coolmath Games Bloxorz - Stage 10",
            "grid": [
                ".oooo.........",
                ".oSoo.ff......",
                ".oo+o.ff..==..",
                "......ff..==.o",
                "......ff..==oX",
                "......oooo==oG",
                "......oooo...o",
                "......oooo...."
            ],
            "switches": [
                {
                    "type": "soft",
                    "pos": [2, 3],
                    "action": "toggle",
                    "bridges": [
                        [2, 10], [2, 11],
                        [3, 10], [3, 11]
                    ],
                    "teleport_cubes": None
                },
                {
                    "type": "heavy",
                    "pos": [4, 13],
                    "action": "permanent",
                    "bridges": [
                        [4, 10], [4, 11],
                        [5, 10], [5, 11]
                    ],
                    "teleport_cubes": None
                }
            ],
            "bridges": [
                {"pos": [2, 10], "initially_open": False},
                {"pos": [2, 11], "initially_open": False},
                {"pos": [3, 10], "initially_open": False},
                {"pos": [3, 11], "initially_open": False},
                {"pos": [4, 10], "initially_open": False},
                {"pos": [4, 11], "initially_open": False},
                {"pos": [5, 10], "initially_open": False},
                {"pos": [5, 11], "initially_open": False}
            ]
        },
        {
            "id": "L4-02",
            "name": "Stage 11 - Split Switch Intro",
            "group": "L4",
            "difficulty": "Combined",
            "source": "Coolmath Games Bloxorz - Stage 11",
            "grid": [
                ".oooo.........o",
                ".oSoY..........",
                ".oooo...==..ooo",
                "........==..oGo",
                "..+.....==..ooo",
                "..oo...........",
                "..oo..........."
            ],
            "switches": [
                {
                    "type": "split",
                    "pos": [1, 4],
                    "action": None,
                    "bridges": None,
                    "teleport_cubes": [[4, 2], [6, 2]]
                },
                {
                    "type": "soft",
                    "pos": [4, 2],
                    "action": "toggle",
                    "bridges": [
                        [2, 8], [2, 9],
                        [3, 8], [3, 9],
                        [4, 8], [4, 9]
                    ],
                    "teleport_cubes": None
                }
            ],
            "bridges": [
                {"pos": [2, 8], "initially_open": False},
                {"pos": [2, 9], "initially_open": False},
                {"pos": [3, 8], "initially_open": False},
                {"pos": [3, 9], "initially_open": False},
                {"pos": [4, 8], "initially_open": False},
                {"pos": [4, 9], "initially_open": False}
            ]
        },
        {
            "id": "L4-03",
            "name": "Stage 12 - Split Remote Coordination",
            "group": "L4",
            "difficulty": "Combined",
            "source": "Coolmath Games Bloxorz - Stage 12",
            "grid": [
                ".ooooo..........",
                ".oSooY..........",
                ".ooooo...==...oo",
                ".........==..oGo",
                "..+......==...oo",
                "..oo..ff........",
                "..oo..ff..+.....",
                "......ff..oo...."
            ],
            "switches": [
                {
                    "type": "split",
                    "pos": [1, 5],
                    "action": None,
                    "bridges": None,
                    "teleport_cubes": [[4, 2], [6, 10]]
                },
                {
                    "type": "soft",
                    "pos": [4, 2],
                    "action": "toggle",
                    "bridges": [
                        [2, 9], [2, 10],
                        [3, 9], [3, 10]
                    ],
                    "teleport_cubes": None
                },
                {
                    "type": "soft",
                    "pos": [6, 10],
                    "action": "toggle",
                    "bridges": [
                        [4, 9], [4, 10]
                    ],
                    "teleport_cubes": None
                }
            ],
            "bridges": [
                {"pos": [2, 9], "initially_open": False},
                {"pos": [2, 10], "initially_open": False},
                {"pos": [3, 9], "initially_open": False},
                {"pos": [3, 10], "initially_open": False},
                {"pos": [4, 9], "initially_open": False},
                {"pos": [4, 10], "initially_open": False}
            ]
        }
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
