"""Ursina prototype renderer (#28).

The GUI layer depends on ``bloxorz.core`` only: it reads states, calls ``Board``, and never
re-implements transitions or search. The real art direction lands in ``theme.md`` later, so every
colour lives in ``theme.py`` as a neutral placeholder.
"""
