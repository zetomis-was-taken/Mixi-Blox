"""The title screen package for the animated boot sequence."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scene import TitleScene


def __getattr__(name: str):
    if name == "TitleScene":
        from .scene import TitleScene

        return TitleScene
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TitleScene"]
