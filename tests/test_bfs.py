"""BFS move optimality, FIFO order, cycle handling and the shared-loop contract (#19)."""

from __future__ import annotations

from collections import deque

import pytest
from search_helpers import FIXTURES, STAGES, replay

from Source.bloxorz.core.contracts import Caps, State
from Source.bloxorz.core.engine import Board
from Source.bloxorz.core.stage import load_stage
from Source.bloxorz.solvers import base, bfs, ucs


class _GraphBoard:
    """A board whose only job is to make the search order visible."""

    nodes: tuple[str, ...] = ()
    edges: dict[str, tuple[str, ...]] = {}

    def __init__(self, _stage) -> None:
        self.states = {name: State((((0, index),),), ()) for index, name in enumerate(self.nodes)}
        self.names = {state: name for name, state in self.states.items}

    def start(self):
        return self.states["S"]
    
    def is_goal(self, state) -> bool:
        return self.names[state] == "G"
    
    def successors(self, state):
        return [(self.states[name], (0, "R")) for name in self.edges.get(self.names[state], ())]
    
    def step_cost(self, state, action, child) -> float:
        return 1.0