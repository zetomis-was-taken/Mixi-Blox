"""Ursina prototype renderer (#28).

The GUI layer depends on ``bloxorz.core`` only: it reads states, calls ``Board``, and never
re-implements transitions or search. Every colour lives in ``theme.py``, and the palette's mapping
to cell kinds is documented in ``docs/gui/theme.md``.
"""
