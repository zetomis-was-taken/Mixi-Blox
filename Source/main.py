"""Entry point. Puts ``Source/`` on ``sys.path`` (§ Layout, rule 1) and reports a stage.

``--gui`` launches the Ursina prototype (#28), booting straight into ``L1-01`` when no ``--stage``
is given. The four solvers (#18-#23) are not here yet, so ``--solver`` still reports that.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

# The prototype's boot level (#28). The GUI loads it when no --stage is given.
DEFAULT_GUI_STAGE = SOURCE / "bloxorz" / "core" / "stages" / "L1-01_long_corridor.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Mixi-Blox: load a stage and show its legal moves."
    )
    parser.add_argument("--stage", metavar="FILE", help="path to a stage JSON file")
    parser.add_argument(
        "--solver",
        choices=("bfs", "dfs", "ucs", "astar"),
        help="algorithm to run (#18-#23)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="launch the Ursina prototype (L1-01 unless --stage is given)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui:
        from bloxorz.gui.app import run

        return run(args.stage or DEFAULT_GUI_STAGE)

    if args.stage is None:
        parser.print_help()
        return 0

    from bloxorz.core.engine import Board, cells
    from bloxorz.core.stage import load_stage

    stage = load_stage(args.stage)
    board = Board(stage)
    start = board.start()
    moves = board.successors(start)
    print(
        f"{stage.id} {stage.name} [{stage.group}] {stage.index.rows}x{stage.index.cols}"
    )
    print(f"start {cells(start)[0]}  goal {stage.index.goal}  legal moves {len(moves)}")
    for state, action in moves:
        print(f"  {action[1]} -> {cells(state)}")
    if args.solver:
        print(f"{args.solver} is not registered yet: solvers land in #18-#23")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
