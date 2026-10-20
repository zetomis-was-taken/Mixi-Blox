"""``load_stage``: the only way a stage enters the program (§ Stage).

The grid is the only source of truth. Everything else the file states is wiring that must agree with
a glyph, and everything a consumer needs is compiled here, once, outside the measured window.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

from bloxorz.core.contracts import Bridge, Cell, Expected, Kind, Stage, StageIndex, Switch

GLYPH_KIND: dict[str, Kind] = {
    ".": "void",
    "o": "floor",
    "S": "start",
    "G": "goal",
    "f": "fragile",
    "=": "bridge",
    "+": "soft",
    "X": "heavy",
    "Y": "split",
}

SWITCH_GLYPH: dict[str, str] = {"soft": "+", "heavy": "X", "split": "Y"}

STAGE_KEYS = {"id", "name", "group", "grid", "source", "expected", "switches", "bridges"}
SWITCH_KEYS = {"type", "pos", "action", "bridges", "teleport_cubes"}
BRIDGE_KEYS = {"pos", "initially_open"}
REQUIRED_KEYS = {"id", "name", "group", "grid"}


class StageError(ValueError):
    """A stage file broke the schema or one of the six loader rules."""


def load_stage(path: str | Path) -> Stage:
    """Read one stage file, check it, and compile its index.

    Raises ``StageError`` with the file and, where the offending token is locatable, the line.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise StageError(f"{path}:{error.lineno}: not valid JSON: {error.msg}") from None
    if not isinstance(raw, dict):
        _fail(path, text, "schema: a stage file holds one JSON object", None)

    _check_keys(path, text, raw)
    grid = _grid(path, text, raw)
    start, goal = _markers(path, text, grid)
    switches = _switches(path, text, raw, grid)
    bridges = _bridges(path, text, raw, grid)
    _check_wiring(path, text, grid, switches, bridges)
    _check_start(path, text, grid, start, bridges)

    rows, cols = len(grid), len(grid[0])
    index = StageIndex(
        rows=rows,
        cols=cols,
        kind=tuple(GLYPH_KIND[glyph] for row in grid for glyph in row),
        bridge_of={bridge.pos: position for position, bridge in enumerate(bridges)},
        switch_at={switch.pos: switch for switch in switches},
        start=start,
        goal=goal,
    )
    return Stage(
        id=_text(path, text, raw, "id"),
        name=_text(path, text, raw, "name"),
        group=_text(path, text, raw, "group"),
        grid=grid,
        source=_optional_text(path, text, raw, "source"),
        expected=_expected(path, text, raw),
        index=index,
        bridges=bridges,
    )


def _fail(path: Path, text: str, message: str, needle: str | None) -> NoReturn:
    raise StageError(f"{_where(path, text, needle)}: {message}")


def _where(path: Path, text: str, needle: str | None) -> str:
    """``file:line`` when the needle is in the file, ``file`` otherwise."""
    if needle is None:
        return str(path)
    position = text.find(needle)
    if position < 0:
        return str(path)
    return f"{path}:{text.count(chr(10), 0, position) + 1}"


def _optional_text(path: Path, text: str, raw: dict[str, object], key: str) -> str | None:
    value = raw.get(key)
    if value is None or isinstance(value, str):
        return value
    _fail(path, text, f"schema: {key!r} must be a string or null", f'"{key}"')
    return None


def _check_keys(path: Path, text: str, raw: dict[str, object]) -> None:
    missing = REQUIRED_KEYS - set(raw)
    if missing:
        _fail(path, text, f"schema: missing {sorted(missing)}", None)
    for derived in ("start", "goal", "rows", "cols", "difficulty"):
        if derived in raw:
            _fail(
                path,
                text,
                f"rule 3: {derived!r} is derived from the grid, so the file must not state it",
                f'"{derived}"',
            )
    unknown = set(raw) - STAGE_KEYS
    if unknown:
        _fail(path, text, f"schema: undeclared keys {sorted(unknown)}", None)


def _text(path: Path, text: str, raw: dict[str, object], key: str) -> str:
    value = raw[key]
    if not isinstance(value, str):
        _fail(path, text, f"schema: {key!r} must be a string", f'"{key}"')
    return value


def _grid(path: Path, text: str, raw: dict[str, object]) -> tuple[str, ...]:
    """Rule 1: as many rows as lines, every line the same length, every glyph known."""
    grid = raw["grid"]
    if not isinstance(grid, list) or not grid:
        _fail(path, text, "rule 1: grid must be a non-empty list of strings", '"grid"')
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, str):
            _fail(path, text, "rule 1: every grid line is a string", '"grid"')
        if len(row) != width:
            _fail(
                path,
                text,
                f"rule 1: ragged grid, expected {width} columns, got {len(row)}",
                f'"{row}"',
            )
        for glyph in row:
            if glyph not in GLYPH_KIND:
                _fail(path, text, f"rule 1: unknown glyph {glyph!r}", f'"{row}"')
    return tuple(grid)


def _markers(path: Path, text: str, grid: tuple[str, ...]) -> tuple[Cell, Cell]:
    """Rule 2: exactly one ``S`` and exactly one ``G``."""
    starts = [(row, col) for row, line in enumerate(grid) for col, g in enumerate(line) if g == "S"]
    goals = [(row, col) for row, line in enumerate(grid) for col, g in enumerate(line) if g == "G"]
    if len(starts) != 1 or len(goals) != 1:
        _fail(
            path,
            text,
            f"rule 2: needs exactly one S and one G, found {len(starts)} and {len(goals)}",
            '"grid"',
        )
    return starts[0], goals[0]


def _switches(
    path: Path, text: str, raw: dict[str, object], grid: tuple[str, ...]
) -> tuple[Switch, ...]:
    entries = raw.get("switches", [])
    if not isinstance(entries, list):
        _fail(path, text, "schema: switches must be a list", '"switches"')
    switches: list[Switch] = []
    for entry in entries:
        if not isinstance(entry, dict):
            _fail(path, text, "schema: every switch is an object", '"switches"')
        _switch_keys(path, text, entry)
        kind = entry["type"]
        if kind not in SWITCH_GLYPH:
            _fail(path, text, f"schema: unknown switch type {kind!r}", '"type"')
        pos = _cell(path, text, entry["pos"], f"switch pos {entry['pos']!r}")
        _on_glyph(path, text, pos, SWITCH_GLYPH[kind], grid, f"{kind} switch")
        bridges = _cells(path, text, entry["bridges"], "switch bridges")
        teleports = entry["teleport_cubes"]
        if kind == "split":
            if not isinstance(teleports, list) or len(teleports) != 2:
                _fail(
                    path,
                    text,
                    "schema: a split switch needs two teleport_cubes",
                    '"teleport_cubes"',
                )
            teleport_cubes: tuple[Cell, Cell] | None = (
                _cell(path, text, teleports[0], "teleport_cubes[0]"),
                _cell(path, text, teleports[1], "teleport_cubes[1]"),
            )
            if bridges is not None:
                _fail(path, text, "schema: a split switch links no bridge", '"bridges"')
        else:
            if bridges is None:
                _fail(path, text, "schema: a bridge switch must name its bridges", '"bridges"')
            teleport_cubes = None
        action = entry["action"]
        if action is not None and action not in {"toggle", "on", "off"}:
            _fail(path, text, f"schema: unknown switch action {action!r}", '"action"')
        if (kind == "split") != (action is None):
            wanted = "no action" if kind == "split" else "an action: 'toggle', 'on' or 'off'"
            _fail(path, text, f"schema: a {kind} switch takes {wanted}", '"action"')
        switches.append(
            Switch(
                type=kind,  # type: ignore[arg-type]
                pos=pos,
                action=action,  # type: ignore[arg-type]
                bridges=bridges,
                teleport_cubes=teleport_cubes,
            )
        )
    return tuple(switches)


def _switch_keys(path: Path, text: str, entry: dict[str, object]) -> None:
    unknown = set(entry) - SWITCH_KEYS
    if unknown:
        _fail(path, text, f"schema: switch has undeclared keys {sorted(unknown)}", '"switches"')
    missing = SWITCH_KEYS - set(entry)
    if missing:
        _fail(
            path,
            text,
            f"schema: switch is missing {sorted(missing)}; unused fields are null, never absent",
            '"switches"',
        )


def _bridges(
    path: Path, text: str, raw: dict[str, object], grid: tuple[str, ...]
) -> tuple[Bridge, ...]:
    entries = raw.get("bridges", [])
    if not isinstance(entries, list):
        _fail(path, text, "schema: bridges must be a list", '"bridges"')
    bridges: list[Bridge] = []
    for entry in entries:
        if not isinstance(entry, dict):
            _fail(path, text, "schema: every bridge is an object", '"bridges"')
        unknown = set(entry) - BRIDGE_KEYS
        if unknown:
            _fail(path, text, f"schema: bridge has undeclared keys {sorted(unknown)}", '"bridges"')
        if "pos" not in entry:
            _fail(path, text, "schema: bridge is missing ['pos']", '"bridges"')
        pos = _cell(path, text, entry["pos"], f"bridge pos {entry['pos']!r}")
        _on_glyph(path, text, pos, "=", grid, "bridge")
        open_at_start = entry.get("initially_open", True)
        if not isinstance(open_at_start, bool):
            _fail(path, text, "schema: initially_open must be true or false", '"initially_open"')
        bridges.append(Bridge(pos=pos, initially_open=open_at_start))
    return tuple(bridges)


def _cells(
    path: Path, text: str, value: object, what: str
) -> tuple[Cell, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        _fail(path, text, f"schema: {what} must be a non-empty list of cells", '"bridges"')
    return tuple(_cell(path, text, item, f"{what} entry {item!r}") for item in value)


def _cell(path: Path, text: str, value: object, what: str) -> Cell:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(part, int) for part in value)
    ):
        _fail(path, text, f"schema: {what} must be [row, col]", '"pos"')
    return (value[0], value[1])


def _on_glyph(
    path: Path, text: str, pos: Cell, glyph: str, grid: tuple[str, ...], what: str
) -> None:
    """Rule 4, first direction: the entry sits on the marker that describes it."""
    row, col = pos
    inside = 0 <= row < len(grid) and 0 <= col < len(grid[0])
    found = grid[row][col] if inside else None
    if found != glyph:
        _fail(
            path,
            text,
            f"rule 4: {what} at {pos} sits on {found!r}, expected {glyph!r}",
            f"[{row}, {col}]" if inside else None,
        )


def _check_wiring(
    path: Path,
    text: str,
    grid: tuple[str, ...],
    switches: tuple[Switch, ...],
    bridges: tuple[Bridge, ...],
) -> None:
    """Rule 4, second direction, and rule 5."""
    for kind, glyph in SWITCH_GLYPH.items():
        markers = sum(line.count(glyph) for line in grid)
        entries = sum(1 for switch in switches if switch.type == kind)
        if markers != entries:
            _fail(
                path,
                text,
                f"rule 4: {markers} {glyph!r} markers need {markers} {kind} entries, found "
                f"{entries}",
                '"switches"',
            )
    markers = sum(line.count("=") for line in grid)
    if markers != len(bridges):
        _fail(
            path,
            text,
            f"rule 4: {markers} '=' markers need {markers} bridge entries, found {len(bridges)}",
            '"bridges"',
        )
    known = {bridge.pos for bridge in bridges}
    for switch in switches:
        for pos in switch.bridges or ():
            if pos not in known:
                _fail(
                    path,
                    text,
                    f"rule 5: switch at {switch.pos} links {pos}, which is not in bridges[]",
                    '"switches"',
                )


def _check_start(
    path: Path, text: str, grid: tuple[str, ...], start: Cell, bridges: tuple[Bridge, ...]
) -> None:
    """Rule 6: the start block stands on a non-void tile that is not a closed bridge.

    Unreachable while ``S`` is its own kind (#17 guarantees one kind per cell), so this guards the
    kind grid rather than the file. Kept because the rule is frozen text.
    """
    row, col = start
    if GLYPH_KIND[grid[row][col]] != "start":
        _fail(path, text, f"rule 6: start {start} is not a start tile", None)
    if GLYPH_KIND[grid[row][col]] == "void":
        _fail(path, text, f"rule 6: start {start} stands on void", None)
    closed = {bridge.pos for bridge in bridges if not bridge.initially_open}
    if start in closed:
        _fail(path, text, f"rule 6: start {start} stands on a closed bridge", None)


def _expected(path: Path, text: str, raw: dict[str, object]) -> Expected | None:
    value = raw.get("expected")
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"optimal_cost"}:
        _fail(
            path,
            text,
            "schema: expected holds optimal_cost and nothing else",
            '"expected"',
        )
    cost = value["optimal_cost"]
    if not isinstance(cost, int | float):
        _fail(path, text, "schema: optimal_cost must be a number", '"optimal_cost"')
    return Expected(optimal_cost=float(cost))
