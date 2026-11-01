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

from bloxorz.core.contracts import Action, Direction, State

from . import theme
from .intro import LoadIntro
from .layout import DIRECTION_VECTORS, Pose, landed_cube_index, poses_for_state, tip_plan


@dataclass(frozen=True)
class _Roll:
    entity: Entity
    pivot: Vec3
    offset: Vec3
    axis: Vec3
    angle: float


class BlockView:
    """Owns the block entities and animates one action at a time."""

    def __init__(
        self, rows: int, cols: int, shader: Shader | None = None, parent: Entity | None = None
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.shader = shader
        # Pieces are parented to the scene so destroying it takes them with it; the parent sits at
        # the origin, so a pose's world position is also its local position.
        self.parent = parent
        self.pieces: list[Entity] = []
        self.active = 0
        self._rest_positions: list[tuple[float, float, float]] = []
        self._roll: _Roll | None = None
        self._tip: _Roll | None = None
        self._tipping: Direction | None = None
        self._tip_elapsed = 0.0
        self._is_falling = False
        self._falling = False
        self._fall_elapsed = 0.0
        self._dropping: frozenset[int] | None = None
        self._elapsed = 0.0
        self._next_state: State | None = None
        self._on_done = None
        self._on_drop = None

    @property
    def animating(self) -> bool:
        return self._roll is not None or self._tip is not None or self._falling

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
        """Rebuild the visible boxes to match ``state`` exactly, cancelling any animation."""
        self._place(state)
        self._roll = None
        self._tip = None
        self._tipping = None
        self._tip_elapsed = 0.0
        self._is_falling = False
        self._falling = False
        self._fall_elapsed = 0.0
        self._dropping = None
        self._on_drop = None

    def _place(self, state: State) -> None:
        """Rebuild the visible boxes at ``state``, leaving a roll or a fall in flight alone."""
        for piece in self.pieces:
            destroy(piece)
        self.pieces = [
            Entity(
                parent=self.parent,
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

    def _begin_fall(self) -> None:
        """Tip over the edge when half the block still has a tile under it, else start the drop."""
        self._roll = None
        tip = self._tip_roll()
        if tip is None:
            self._start_fall()
            return
        self._tip = tip
        self._tip_elapsed = 0.0

    def _tip_roll(self) -> _Roll | None:
        """The quarter-turn a half-supported block makes before it drops, if it makes one."""
        if self._tipping is None or self._next_state is None:
            return None
        pose = poses_for_state(self._next_state, self.rows, self.cols)[0]
        tip = tip_plan(pose, self._tipping)
        return _Roll(
            self.pieces[0], Vec3(*tip.pivot), Vec3(*tip.offset), Vec3(*tip.axis), tip.angle
        )

    def _start_fall(self) -> None:
        """Send the pieces now resting on the fatal tile down and out of view."""
        self._roll = None
        self._falling = True
        self._fall_elapsed = 0.0
        drop = self._on_drop
        self._on_drop = None
        if drop is not None:
            drop()

    def _paint(self) -> None:
        """Colour the pieces by which cube is active; a single block is always active."""
        for number, piece in enumerate(self.pieces):
            piece.color = theme.BLOCK if number == self.active else theme.BLOCK_IDLE

    def update_intro(self, intro: LoadIntro) -> None:
        """Drop the block in from above the board, once the tiles have finished loading."""
        drop = (1.0 - intro.player_progress()) * intro.timing.player_drop
        for piece, (x, y, z) in zip(self.pieces, self._rest_positions):
            piece.position = (x, y + drop, z)

    def fall(
        self,
        start: State,
        fatal_state: State,
        action: Action,
        on_done,
        on_drop=None,
        dropping: frozenset[int] | None = None,
        tipping: Direction | None = None,
    ) -> None:
        """Roll to ``fatal_state``, tip off the edge if it is only half over the hole, then drop.

        ``on_drop`` fires on the frame the drop starts, so whatever the block was standing on — a
        fragile tile — can fall with it. ``dropping`` names the pieces with nothing left under them;
        ``None`` drops them all, and a split stage passes the one cube that left the platform so the
        other keeps standing. ``tipping`` is the direction of the hole under half of a lying block:
        that block tips about the edge first, so it never drops through the tile it still rests on.
        """
        self._is_falling = True
        self._dropping = dropping
        self._tipping = tipping
        self._on_drop = on_drop
        self.animate(start, fatal_state, action, on_done)

    def animate(
        self,
        start: State,
        next_state: State,
        action: Action,
        on_done,
    ) -> None:
        """Roll from ``start`` to ``next_state``.

        Every unsplit roll and every split cube's own roll is animated. The landing is looked up by
        the cells the cube rolled onto rather than by the action's index, because the state orders
        its cubes by cell and one action can swap their indices. A transition no roll can express —
        a split switch, a merge, a teleport — snaps to the new pose.
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
            # A split action rolls just the named cube; the other one stays put. Its landing pose
            # is the one whose cube holds the cells it rolled onto, not necessarily the same index.
            index = action[0]
            target = landed_cube_index(start, next_state, action)
            if target is not None:
                plan = self._plan_roll(start_poses[index], end_poses[target], action[1])
                if plan is not None:
                    self._roll = _Roll(self.pieces[index], *plan)
                    return

        # Split switch / merge: no roll to derive, so show the landed pose immediately.
        if self._is_falling:
            self._place(next_state)
            self._begin_fall()
            return
        self.sync(next_state)
        self._finish()

    def update(self, dt: float) -> None:
        if self._tip is not None:
            self._tip_elapsed += dt
            t = min(self._tip_elapsed / theme.ROLL_SECONDS, 1.0)
            rotation = Quat()
            rotation.setFromAxisAngle(self._tip.angle * t, self._tip.axis)
            self._tip.entity.position = self._tip.pivot + rotation.xform(self._tip.offset)
            self._tip.entity.quaternion = rotation
            if t >= 1.0:
                self._tip = None
                self._rest_positions = [tuple(piece.position) for piece in self.pieces]
                self._start_fall()
            return

        if self._falling:
            self._fall_elapsed += dt
            t = min(self._fall_elapsed / theme.FALL_SECONDS, 1.0)
            drop = t * t * theme.FALL_DISTANCE
            for index, (piece, rest) in enumerate(zip(self.pieces, self._rest_positions)):
                if self._dropping is not None and index not in self._dropping:
                    continue
                piece.position = (rest[0], rest[1] - drop, rest[2])
            if t >= 1.0:
                self._falling = False
                self._is_falling = False
                self._finish()
            return

        if self._roll is None:
            return

        self._elapsed += dt
        t = min(self._elapsed / theme.ROLL_SECONDS, 1.0)
        rotation = Quat()
        rotation.setFromAxisAngle(self._roll.angle * t, self._roll.axis)
        self._roll.entity.position = self._roll.pivot + rotation.xform(self._roll.offset)
        self._roll.entity.quaternion = rotation

        if t >= 1.0:
            if self._is_falling:
                self._place(self._next_state)
                self._begin_fall()
                return
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
