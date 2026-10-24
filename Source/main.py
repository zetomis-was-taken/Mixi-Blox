"""Load a stage or run a solver through the frozen API; GUI remains separate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Mixi-Blox: inspect a stage or run a search algorithm."
    )
    parser.add_argument("--stage", metavar="FILE", help="path to a stage JSON file")
    parser.add_argument(
        "--solver",
        choices=("bfs", "dfs", "ucs", "astar"),
        help="algorithm to run (currently ucs, astar, bfs, dfs)",
    )
    parser.add_argument("--node-cap", type=int, help="maximum completed expansions")
    parser.add_argument("--time-cap", type=float, help="search deadline in seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.stage is None:
        if args.solver:
            parser.error("--solver requires --stage")
        parser.print_help()
        return 0

    from dataclasses import asdict

    from bloxorz.core.contracts import Caps
    from bloxorz.core.engine import Board, cells
    from bloxorz.core.stage import StageError, load_stage
    from bloxorz.solvers import astar, bfs, dfs, ucs

    try:
        stage = load_stage(args.stage)
        if args.solver:
            solvers = {
                "bfs": bfs.solve,
                "dfs": dfs.solve,
                "ucs": ucs.solve,
                "astar": astar.solve,
            }
            if args.solver not in solvers:
                parser.error(f"{args.solver} is not registered yet")
            result = solvers[args.solver](stage, Caps(args.node_cap, args.time_cap))
            print(json.dumps(asdict(result), ensure_ascii=True))
            return 0 if result.status == "solved" else 1
    except (StageError, OSError, ValueError) as exc:
        parser.error(str(exc))
    board = Board(stage)
    start = board.start()
    moves = board.successors(start)
    print(f"{stage.id} {stage.name} [{stage.group}] {stage.index.rows}x{stage.index.cols}")
    print(f"start {cells(start)[0]}  goal {stage.index.goal}  legal moves {len(moves)}")
    for state, action in moves:
        print(f"  {action[1]} -> {cells(state)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
