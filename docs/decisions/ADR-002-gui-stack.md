# ADR-002: Use Ursina for the 3D renderer

## Status

Accepted

## Date

2026-10-18

## Context

§3.1 and §3.7 require a 3D GUI, and FAQ Q4 requires the Solve buttons to roll the block to the goal themselves. The stack has to be fixed before GUI code is written, because the language and the process boundary determine how the GUI reaches the solvers.

## Decision

Ursina (Python, Panda3D-backed), as proposed in #4. GUI owner: **zetomis-was-taken**.

Staying in Python means the GUI reaches the solvers through a coarse entry point — stage and algorithm in, path and stats out — that is a function call rather than a protocol: no schema to version, no second language on a 15-day schedule. `State` needs no codec, because the boundary carries a stage, not a state. Ursina is a library rather than a game, which keeps "Reimplement the Game" (§3.1) genuinely ours. Visual polish is the accepted tradeoff.

The renderer never constructs states and never supplies `successors`/`is_goal`.

## Alternatives Considered

### Pygame

- Pros: mature and minimal, 2D drawing is enough for a grid, and it is the stack most likely already known.
- Cons: 2D only — a 3D block would be hand-rolled isometric projection, with no camera, lighting or scene graph, and the three orientations would be drawn by hand.
- Rejected: §3.1/§3.7 ask for a 3D GUI; the projection work is exactly the part that costs schedule.

### Web renderer (three.js)

- Pros: best visual result, free camera and lighting.
- Cons: a second language plus a wire boundary to version, on top of a renderer to write.
- Rejected: the 15-day schedule has no room for a protocol layer that buys only polish.

## Consequences

- The coarse entry point lands before GUI work starts, even though it is only a function call: it keeps the renderer off engine internals and is the shape a network boundary would need, so changing language later replaces a call, not a layer.
- Ursina owns the window and the main loop; the solvers stay engine-agnostic and testable headless.
- Visual polish is capped by what Ursina gives for free; no time is budgeted for asset work.
- Deferred to the GUI PR: a trivial scene that renders, with the block distinguishable in all three orientations (#4).
