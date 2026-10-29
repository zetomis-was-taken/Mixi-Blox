"""Solver menu package for Bloxorz GUI.

Provides a top-right hamburger icon and dropdown algorithm selector.
"""

from __future__ import annotations

from .dropdown import DropdownMenu
from .hamburger_button import HamburgerButton
from .menu import SolverMenu

# Backward-compatibility alias
SolverPanel = SolverMenu

__all__ = ["DropdownMenu", "HamburgerButton", "SolverMenu", "SolverPanel"]

