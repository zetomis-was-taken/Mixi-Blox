"""Independent board replay and reverse-graph oracle shared by solver tests."""

from __future__ import annotations

from collections import defaultdict
from heapq import heappop, heappush
from itertools import count
from pathlib import Path

from bloxorz.core.contracts import State
from bloxorz.core.engine import Board

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source/bloxorz/core/stages"
FIXTURES = ROOT / "tests/fixtures"
# The hand-solved set (#21). Derived from the directory so a new fixture is picked up by every
# solver test at once instead of needing the same literal list edited in four places.
FIXTURE_IDS = tuple(path.stem.split("_")[0] for path in sorted(FIXTURES.glob("FIX-*.json")))


def replay(board: Board, path: tuple) -> tuple[State, float]:
    state, cost = board.start(), 0.0
    for action in path:
        child = {move: state for state, move in board.successors(state)}[action]
        cost += board.step_cost(state, action, child)
        state = child
    return state, cost


def remaining_costs(board: Board) -> tuple[set[State], dict[State, float]]:
    """Enumerate the reachable graph, then solve backwards from every goal."""
    seen = {board.start()}
    pending = list(seen)
    reverse = defaultdict(list)
    goals = []
    while pending:
        state = pending.pop()
        if board.is_goal(state):
            goals.append(state)
        for child, action in board.successors(state):
            reverse[child].append((state, board.step_cost(state, action, child)))
            if child not in seen:
                seen.add(child)
                pending.append(child)
    serial = count()
    distance = {goal: 0.0 for goal in goals}
    frontier = [(0.0, next(serial), goal) for goal in goals]
    while frontier:
        cost, _, state = heappop(frontier)
        if cost != distance[state]:
            continue
        for previous, weight in reverse[state]:
            candidate = cost + weight
            if candidate < distance.get(previous, float("inf")):
                distance[previous] = candidate
                heappush(frontier, (candidate, next(serial), previous))
    return seen, distance


class GraphBoard:
    """A directed graph where first discovery gives an expensive path."""

    costs = {("S", "A"): 5, ("S", "B"): 1, ("B", "A"): 1, ("A", "G"): 1, ("B", "G"): 20}

    def __init__(self, _stage) -> None:
        self.states = {name: State((((0, index),),), ()) for index, name in enumerate("SABG")}
        self.names = {state: name for name, state in self.states.items()}

    def start(self):
        return self.states["S"]

    def is_goal(self, state):
        return state == self.states["G"]

    def successors(self, state):
        edges = {"S": [("A", "R"), ("B", "D")], "B": [("A", "L"), ("G", "D")], "A": [("G", "R")]}
        return [
            (self.states[name], (0, direction))
            for name, direction in edges.get(self.names[state], [])
        ]

    def step_cost(self, state, action, child):
        return float(self.costs[self.names[state], self.names[child]])
