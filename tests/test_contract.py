"""Enforcement for the rules in ``docs/contracts.md`` and ``CONTRIBUTING.md``.

These checks are structural: where a module lives, what it imports, and which names it may define.
Nothing here imports ``bloxorz``, so the suite runs while the package is still half-built, and a
rule broken by a future module fails on that module's pull request instead of quietly afterwards.

Each test names the clause it enforces, so a red run reads as a rule and not as a mystery
assertion. Anything that depends on code that does not exist yet skips with a reason rather than
passing vacuously.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Source"
PACKAGE = SOURCE / "bloxorz"

# contracts.md § Layout and rule 4: one definition per frozen type, in the module named here.
# `Board` is the one frozen type that is not in contracts.py — it is stage-scoped and lives beside
# the transition model it owns.
FROZEN_DEFINITIONS = {
    "State": "Source/bloxorz/core/contracts.py",
    "Stage": "Source/bloxorz/core/contracts.py",
    "StageIndex": "Source/bloxorz/core/contracts.py",
    "Counts": "Source/bloxorz/core/contracts.py",
    "Stats": "Source/bloxorz/core/contracts.py",
    "SearchResult": "Source/bloxorz/core/contracts.py",
    "Caps": "Source/bloxorz/core/contracts.py",
    "Expected": "Source/bloxorz/core/contracts.py",
    "Switch": "Source/bloxorz/core/contracts.py",
    "Bridge": "Source/bloxorz/core/contracts.py",
    "Board": "Source/bloxorz/core/engine.py",
}

# contracts.md § Board, rule 3: dependencies point one way. `solvers -> core`, `bench -> core +
# solvers`, `gui -> core + solvers`, and nothing imports bench or gui.
FORBIDDEN_IMPORTS = {
    "core": ("bloxorz.solvers", "bloxorz.bench", "bloxorz.gui"),
    "solvers": ("bloxorz.bench", "bloxorz.gui"),
    "": ("bloxorz.bench", "bloxorz.gui"),  # anything outside bench/ and gui/
}

# Rule 1: `Source/` reaches sys.path from the entry point, pytest.ini and CI — never from a module.
SYSPATH_ALLOWED = {"Source/main.py", "tests/conftest.py"}

# Rule 5: no clocks or allocators outside bench/. `perf_counter` is also allowed in solvers/, which
# implements the `Caps.time_s` deadline in the § Solver API loop; what must never happen is a
# solver measuring itself or the engine timing anything.
CLOCK_ALLOWED = {"bench", "solvers"}
ALLOCATOR_ALLOWED = {"bench"}

# Its own kind of rule: harness output belongs in Report/data/, and there is no search/ directory.
FORBIDDEN_AT_ROOT = (
    "core",
    "benchmark",
    "benchmark_results.csv",
    "benchmark_results.json",
    "Source/bloxorz/search",
)

# contracts.md § Stage: the grid is the only source of truth, and the loader derives the rest.
STAGE_KEYS = {"id", "name", "group", "grid", "source", "expected", "switches", "bridges"}
DERIVED_STAGE_FIELDS = {"rows", "cols", "start", "goal", "difficulty"}


def _python_files(*roots: Path) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if root.exists():
            found.extend(p for p in root.rglob("*.py") if ".venv" not in p.parts)
    return sorted(found)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _layer(path: Path) -> str:
    """The package layer a file sits in: core, solvers, bench, gui, or "" for anything else."""
    parts = path.relative_to(PACKAGE).parts
    return parts[0] if len(parts) > 1 and parts[0] in {"core", "solvers", "bench", "gui"} else ""


def _skip_unless_package() -> None:
    if not PACKAGE.is_dir():
        pytest.skip("Source/bloxorz/ does not exist yet")


def test_frozen_types_are_defined_once() -> None:
    """contracts.md § Layout, rule 4."""
    _skip_unless_package()
    violations = []
    for path in _python_files(PACKAGE):
        for node in _parse(path).body:
            if isinstance(node, ast.ClassDef) and node.name in FROZEN_DEFINITIONS:
                if _rel(path) != FROZEN_DEFINITIONS[node.name]:
                    violations.append(
                        f"{_rel(path)}:{node.lineno} redefines {node.name}; "
                        f"import it from {FROZEN_DEFINITIONS[node.name]}"
                    )
    assert not violations, "\n".join(violations)


def test_imports_point_one_way() -> None:
    """contracts.md § Board, rule 3."""
    _skip_unless_package()
    violations = []
    for path in _python_files(PACKAGE):
        forbidden = FORBIDDEN_IMPORTS.get(_layer(path), ())
        for node in ast.walk(_parse(path)):
            module = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden):
                        module = alias.name
                        break
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(forbidden):
                    module = node.module
            if module:
                violations.append(f"{_rel(path)}:{node.lineno} imports {module}")
    assert not violations, "\n".join(violations)


def test_sys_path_is_put_in_one_place() -> None:
    """Rule 1: the entry point, pytest.ini and CI — not every module."""
    violations = []
    for path in _python_files(SOURCE, ROOT / "tools", ROOT / "tests"):
        if _rel(path) in SYSPATH_ALLOWED:
            continue
        for node in ast.walk(_parse(path)):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            target = node.func.value
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "sys"
                and target.attr == "path"
                and node.func.attr in {"insert", "append", "extend"}
            ):
                violations.append(f"{_rel(path)}:{node.lineno} mutates sys.path")
    assert not violations, "\n".join(violations)


def test_clocks_and_allocators_stay_in_bench() -> None:
    """Rule 5, as narrowed by the `Caps.time_s` deadline in § Solver API."""
    _skip_unless_package()
    violations = []
    for path in _python_files(PACKAGE):
        layer = _layer(path)
        for node in ast.walk(_parse(path)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name == "tracemalloc" and layer not in ALLOCATOR_ALLOWED:
                    violations.append(f"{_rel(path)}:{node.lineno} imports tracemalloc")
                if name == "time" and layer not in CLOCK_ALLOWED:
                    violations.append(f"{_rel(path)}:{node.lineno} imports time")
    assert not violations, "\n".join(violations)


def test_root_holds_no_derived_artifacts() -> None:
    """Harness output belongs in Report/data/, and the solver package is solvers/, not search/."""
    present = [name for name in FORBIDDEN_AT_ROOT if (ROOT / name).exists()]
    assert not present, "these belong elsewhere: " + ", ".join(present)


def test_stage_files_match_the_frozen_schema() -> None:
    """contracts.md § Stage: the grid is the only source of truth, not a place to cache results."""
    stages = PACKAGE / "core" / "stages"
    if not stages.is_dir():
        pytest.skip("no stage files yet")
    violations = []
    for path in sorted(stages.glob("*.json")):
        stage = json.loads(path.read_text(encoding="utf-8"))
        name = path.name
        unexpected = set(stage) - STAGE_KEYS
        derived = set(stage) & DERIVED_STAGE_FIELDS
        if unexpected:
            violations.append(f"{name}: undeclared keys {sorted(unexpected)}")
        if derived:
            violations.append(f"{name}: derives {sorted(derived)} from the grid")
        grid = stage.get("grid") or []
        if len({len(row) for row in grid}) > 1:
            violations.append(f"{name}: ragged grid")
        flat = "".join(grid)
        if flat.count("S") != 1 or flat.count("G") != 1:
            violations.append(
                f"{name}: needs exactly one S and one G, has "
                f"{flat.count('S')} and {flat.count('G')}"
            )
    assert not violations, "\n".join(violations)
