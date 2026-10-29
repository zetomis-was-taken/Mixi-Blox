"""The level's Solve control: backward-compatible shim.

Re-exports ``SolverPanel`` from ``bloxorz.gui.solver_menu``.
"""

from __future__ import annotations

from .solver_menu import SolverPanel

__all__ = ["SolverPanel"]
