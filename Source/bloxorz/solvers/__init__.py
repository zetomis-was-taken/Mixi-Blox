"""Search algorithms for a compiled :mod:`bloxorz` stage.

The shared loop lives in :mod:`bloxorz.solvers.base`. Each algorithm module adds one frontier
ordering and exposes the frozen ``solve(stage, caps)`` (#18).
"""
