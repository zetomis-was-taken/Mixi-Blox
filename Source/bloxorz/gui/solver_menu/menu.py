"""The SolverMenu entity combining the hamburger button and dropdown (Ursina).

Coordinates opening and closing the menu, reporting busy states, and triggering solver runs.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, camera

from .dropdown import DropdownMenu
from .hamburger_button import HamburgerButton


class SolverMenu(Entity):
    """The complete solver control: top-right hamburger icon and dropdown algorithm options."""

    def __init__(self, algorithms: tuple[str, ...], on_pick: Callable[[str], None]) -> None:
        super().__init__(name="solver-menu", parent=camera.ui)
        self.algorithms = algorithms
        self.on_pick = on_pick
        self._shown = False

        self.hamburger = HamburgerButton(parent=self, on_toggle=self.toggle)
        self.dropdown = DropdownMenu(
            parent=self,
            algorithms=algorithms,
            on_pick=self._handle_pick,
            on_close=self.close,
        )

        # Built initially hidden
        self.enabled = False

    @property
    def is_open(self) -> bool:
        """Whether the algorithm dropdown is currently expanded."""
        return bool(self.dropdown.enabled)

    def show(self) -> None:
        """Show the solver hamburger button (dropdown starts closed)."""
        if self._shown:
            return
        self._shown = True
        self.enabled = True
        self.dropdown.enabled = False

    def hide(self) -> None:
        """Hide both the hamburger button and dropdown."""
        if not self._shown:
            return
        self._shown = False
        self.dropdown.enabled = False
        self.enabled = False

    def toggle(self) -> None:
        """Toggle the dropdown open or closed."""
        if not self._shown:
            return
        if self.is_open:
            self.close()
        else:
            self.open()

    def open(self) -> None:
        """Open the dropdown menu."""
        if not self._shown:
            return
        self.dropdown.enabled = True

    def close(self) -> None:
        """Close the dropdown menu."""
        self.dropdown.enabled = False

    def set_busy(self, algorithm: str | None) -> None:
        """Update busy status on the hamburger icon and dropdown."""
        self.hamburger.set_busy(algorithm is not None)
        self.dropdown.set_busy(algorithm)

    def _handle_pick(self, algorithm: str) -> None:
        """Start a run through the callback."""
        if not self._shown:
            return
        self.on_pick(algorithm)

