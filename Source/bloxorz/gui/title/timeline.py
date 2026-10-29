"""Pure-Python timeline mathematics for the title screen animation keyframes.

No Ursina imports: this module is purely algebraic and unit-testable headlessly.
"""

from __future__ import annotations

# Alignment Anchor: Starting X position for Title and Menu buttons (widened)
ANCHOR_LEFT_X = -0.56

# Offscreen starting position for sliding elements
OFFSCREEN_LEFT_X = -1.15

# Keyframe Boundaries (in seconds)
KF1_END = 0.50          # Keyframe 1: Title snaps in at top-left, Player appears at center
KF2_START = 0.50
KF2_END = 1.00          # Keyframe 2: Player block slides to center-right
KF3A_START = 1.00
KF3A_END = 1.30         # Keyframe 3a: "PLAY" button slides in from left to ANCHOR_LEFT_X
KF3B_START = 1.20
KF3B_END = 1.50         # Keyframe 3b: "QUIT" button slides in from left to ANCHOR_LEFT_X
READY_TIME = 1.60       # Interactive ready time

# Target Coordinates (camera.ui space)
TITLE_TARGET_Y = 0.28
PLAY_TARGET_Y = -0.02
QUIT_TARGET_Y = -0.19

BLOCK_TARGET_Y = (PLAY_TARGET_Y + QUIT_TARGET_Y) / 2.0

BLOCK_INIT_POS = (0.00, BLOCK_TARGET_Y, 0.00)     # Initial center staging
BLOCK_REST_POS = (0.34, BLOCK_TARGET_Y, 0.00)     # Settled center-right (widened)


def clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp val to [low, high]."""
    return max(low, min(high, val))


def ease_out_back(t: float, s: float = 1.70158) -> float:
    """Snappy overshoot easing (out-back)."""
    t = clamp(t) - 1.0
    return 1.0 + (s + 1.0) * (t ** 3) + s * (t ** 2)


def ease_out_cubic(t: float) -> float:
    """Standard cubic ease-out."""
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def title_position(elapsed: float) -> tuple[float, float]:
    """Calculate Title (X, Y) at a given elapsed time.

    Slides from OFFSCREEN_LEFT_X to ANCHOR_LEFT_X during Keyframe 1.
    """
    if elapsed <= 0.0:
        return (OFFSCREEN_LEFT_X, TITLE_TARGET_Y)
    if elapsed >= KF1_END:
        return (ANCHOR_LEFT_X, TITLE_TARGET_Y)
    progress = elapsed / KF1_END
    eased = ease_out_back(progress, s=1.2)
    x = OFFSCREEN_LEFT_X + (ANCHOR_LEFT_X - OFFSCREEN_LEFT_X) * eased
    return (x, TITLE_TARGET_Y)


def player_block_position(elapsed: float) -> tuple[float, float, float]:
    """Calculate Player Block 3D center position across Keyframes 1 and 2."""
    if elapsed <= KF2_START:
        return BLOCK_INIT_POS
    if elapsed >= KF2_END:
        return BLOCK_REST_POS
    local_t = (elapsed - KF2_START) / (KF2_END - KF2_START)
    eased = ease_out_cubic(local_t)
    x = BLOCK_INIT_POS[0] + (BLOCK_REST_POS[0] - BLOCK_INIT_POS[0]) * eased
    return (x, BLOCK_REST_POS[1], BLOCK_REST_POS[2])


def player_block_scale(elapsed: float) -> float:
    """Calculate Player Block pop-in scale during Keyframe 1."""
    if elapsed <= 0.0:
        return 0.0
    if elapsed >= KF1_END:
        return 1.0
    progress = elapsed / KF1_END
    return ease_out_back(progress, s=1.4)


def play_button_x(elapsed: float) -> float:
    """Calculate 'PLAY' button X coordinate during Keyframe 3a."""
    if elapsed <= KF3A_START:
        return OFFSCREEN_LEFT_X
    if elapsed >= KF3A_END:
        return ANCHOR_LEFT_X
    local_t = (elapsed - KF3A_START) / (KF3A_END - KF3A_START)
    eased = ease_out_back(local_t, s=1.2)
    return OFFSCREEN_LEFT_X + (ANCHOR_LEFT_X - OFFSCREEN_LEFT_X) * eased


def quit_button_x(elapsed: float) -> float:
    """Calculate 'QUIT' button X coordinate during Keyframe 3b."""
    if elapsed <= KF3B_START:
        return OFFSCREEN_LEFT_X
    if elapsed >= KF3B_END:
        return ANCHOR_LEFT_X
    local_t = (elapsed - KF3B_START) / (KF3B_END - KF3B_START)
    eased = ease_out_back(local_t, s=1.2)
    return OFFSCREEN_LEFT_X + (ANCHOR_LEFT_X - OFFSCREEN_LEFT_X) * eased


def is_interactive(elapsed: float) -> bool:
    """Whether user hover/click interaction is active (post-animation)."""
    return elapsed >= READY_TIME
