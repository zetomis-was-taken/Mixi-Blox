"""The player's block, shown as one box or two cubes.

Movement is a real roll: the box rotates about the bottom edge it is tipping over, so its rotation
is driven by the translation instead of being a canned loop. The pivot and the rotation sign are
derived from the start and end poses, which also keeps the animation honest for the 1x1x2 block
(one quarter-turn per action).
"""

from __future__ import annotations

from dataclasses import dataclass

from panda3d.core import Quat, Vec3
from ursina import Entity, Shader, destroy

from bloxorz.core.contracts import Action, State

from . import theme
from .intro import LoadIntro
from .layout import DIRECTION_VECTORS, Pose, poses_for_state


@dataclass(frozen=True)
class _Roll:
    entity: Entity
    pivot: Vec3
    offset: Vec3
    axis: Vec3
    angle: float


class BlockView:
    """Owns the block entities and animates one action at a time."""

    def __init__(self, rows: int, cols: int, shader: Shader | None = None) -> None:
        self.rows = rows
        self.cols = cols
        self.shader = shader
        self.pieces: list[Entity] = []
        self.active = 0
        self._rest_positions: list[tuple[float, float, float]] = []
        self._roll: _Roll | None = None
        self._elapsed = 0.0
        self._next_state: State | None = None
        self._on_done = None

    @property
    def animating(self) -> bool:
        return self._roll is not None

    def set_active(self, index: int) -> None:
        """Tint the cubes: the one that takes the next input keeps the strong accent.

        The two split cubes are interchangeable, so the player has to see which one moves next. An
        unsplit block is always active, so the call is a no-op there.
        """
        if index == self.active:
            return
        self.active = index
        self._paint()

    def sync(self, state: State) -> None:
        """Rebuild the visible boxes to match ``state`` exactly."""
        for piece in self.pieces:
            destroy(piece)
        self.pieces = [
            Entity(
                name=f"block-{number}",
                model="cube",
                color=theme.BLOCK,
                scale=pose.scale,
                position=pose.center,
                shader=self.shader,
            )
            for number, pose in enumerate(poses_for_state(state, self.rows, self.cols))
        ]
        self._rest_positions = [tuple(piece.position) for piece in self.pieces]
        self._paint()
        self._roll = None

    def _paint(self) -> None:
        """Colour the pieces by which cube is active; a single block is always active."""
        for number, piece in enumerate(self.pieces):
            piece.color = theme.BLOCK if number == self.active else theme.BLOCK_IDLE

    def update_intro(self, intro: LoadIntro) -> None:
        """Drop the block in from above the board, once the tiles have finished loading."""
        drop = (1.0 - intro.player_progress()) * intro.timing.player_drop
        for piece, (x, y, z) in zip(self.pieces, self._rest_positions):
            piece.position = (x, y + drop, z)

    def animate(
        self,
        start: State,
        next_state: State,
        action: Action,
        on_done,
    ) -> None:
        """Roll from ``start`` to ``next_state``.

        Only the common unsplit action and a split cube's own roll are animated. Split/merge/
        teleport transitions (which ``L1-01`` does not use) snap to the new pose; polishing those
        is part of #28.
        """
        start_poses = poses_for_state(start, self.rows, self.cols)
        end_poses = poses_for_state(next_state, self.rows, self.cols)
        self._next_state = next_state
        self._on_done = on_done
        self._elapsed = 0.0

        if len(start_poses) == len(end_poses) == 1:
            plan = self._plan_roll(start_poses[0], end_poses[0], action[1])
            if plan is not None:
                self._roll = _Roll(self.pieces[0], *plan)
                return
        elif len(start_poses) == len(end_poses) == 2:
            # A split action rolls just the named cube; the other one stays put.
            index = action[0]
            plan = self._plan_roll(start_poses[index], end_poses[index], action[1])
            if plan is not None:
                self._roll = _Roll(self.pieces[index], *plan)
                return

        # Split switch / merge: no roll to derive, so show the landed pose immediately.
        self.sync(next_state)
        self._finish()

    def update(self, dt: float) -> None:
        if self._roll is None:
            return

        self._elapsed += dt
        t = min(self._elapsed / theme.ROLL_SECONDS, 1.0)
        rotation = Quat()
        rotation.setFromAxisAngle(self._roll.angle * t, self._roll.axis)
        self._roll.entity.position = self._roll.pivot + rotation.xform(self._roll.offset)
        self._roll.entity.quaternion = rotation

        if t >= 1.0:
            self.sync(self._next_state)
            self._finish()

    def _finish(self) -> None:
        callback = self._on_done
        self._on_done = None
        if callback is not None:
            callback()

    def _plan_roll(
        self, start: Pose, end: Pose, direction: str
    ) -> tuple[Vec3, Vec3, Vec3, float] | None:
        """Pivot, centre offset, axis and signed 90-degree angle for one roll."""
        dx, dz = DIRECTION_VECTORS[direction]
        cx, cy, cz = start.center
        half_x, _, half_z = (length / 2.0 for length in start.scale)

        if dx:
            pivot = Vec3(cx + dx * half_x, 0.0, cz)
            axis = Vec3(0.0, 0.0, 1.0)
        else:
            pivot = Vec3(cx, 0.0, cz + dz * half_z)
            axis = Vec3(1.0, 0.0, 0.0)

        offset = Vec3(cx, cy, cz) - pivot
        destination = Vec3(*end.center)

        for angle in (90.0, -90.0):
            rotation = Quat()
            rotation.setFromAxisAngle(angle, axis)
            landed = pivot + rotation.xform(offset)
            if (landed - destination).length() < 1e-3:
                return pivot, offset, axis, angle
        return None
