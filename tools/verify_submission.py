#!/usr/bin/env python3
"""
Submission Verification Tool - CSC14003 (Bloxorz Solver)
Performs automated pre-flight checks against assignment rubrics:
1. Validates directory structure (Source/, Report.pdf, requirements.txt, README.md).
2. Detects forbidden artifacts (__pycache__, .venv, .git, temp files).
3. Ensures total package size is under 20MB.
4. Scans for the professor's prompt-injection trap sentence ("mèo lượng tử" / "quantum cat").
"""

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20MB limit per rubric

FORBIDDEN_PATTERNS = [
    r"__pycache__",
    r"\.pytest_cache",
    r"\.mypy_cache",
    r"\.ruff_cache",
    r"\.venv",
    r"venv",
    r"\.git\b",
    r"\.DS_Store",
    r"Thumbs\.db",
    r"\.pyc$",
    r"\.pyo$"
]

TRAP_KEYWORDS = [
    r"mèo\s+lượng\s+tử",
    r"quantum\s+cat",
    r"định\s+lý\s+con\s+mèo"
]

def check_structure(root_dir: Path) -> list[str]:
    """Validates required files according to assignment specifications."""
    errors = []
    
    # Check Source folder or main.py
    has_main = (root_dir / "Source" / "main.py").exists() or (root_dir / "main.py").exists()
    if not has_main:
        errors.append("MISSING: Entry point 'main.py' (expected in Source/main.py or main.py).")

    # Check README.md
    if not (root_dir / "README.md").exists():
        errors.append("MISSING: 'README.md' at project root.")

    # Check requirements.txt
    if not (root_dir / "requirements.txt").exists():
        errors.append("MISSING: 'requirements.txt' at project root.")

    # Check Report
    has_report = (
        (root_dir / "Report.pdf").exists() or
        (root_dir / "Report" / "Report.pdf").exists() or
        (root_dir / "report" / "main.pdf").exists()
    )
    if not has_report:
        errors.append("WARNING/MISSING: 'Report.pdf' not found yet (remember to compile LaTeX to PDF before submission).")

    return errors


def check_forbidden_artifacts(root_dir: Path, ignore_git: bool = False) -> list[str]:
    """Scans for unwanted cache and virtual environment files."""
    violations = []
    for path in root_dir.rglob("*"):
        rel_str = str(path.relative_to(root_dir)).replace("\\", "/")
        if ignore_git and (rel_str == ".git" or rel_str.startswith(".git/")):
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, rel_str, re.IGNORECASE):
                violations.append(f"FORBIDDEN ARTIFACT: {rel_str}")
                break
    return violations


def scan_for_trap_keywords(root_dir: Path) -> list[str]:
    """Scans text and pdf files for the watermarking trap instruction."""
    traps_found = []
    text_extensions = {".md", ".py", ".tex", ".txt", ".json", ".html"}
    
    for path in root_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in text_extensions:
            # Skip verify_submission.py itself to avoid self-flagging
            if path.name == "verify_submission.py":
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for trap in TRAP_KEYWORDS:
                    if re.search(trap, content, re.IGNORECASE):
                        traps_found.append(f"CRITICAL: Found trap keyword '{trap}' in {path.relative_to(root_dir)}!")
            except Exception:
                pass
    return traps_found


def check_size(target_path: Path) -> tuple[int, bool]:
    """Calculates total size in bytes and checks against the 20MB limit."""
    if target_path.is_file():
        total_size = target_path.stat().st_size
    else:
        total_size = sum(f.stat().st_size for f in target_path.rglob("*") if f.is_file())
    
    is_valid = total_size <= MAX_SIZE_BYTES
    return total_size, is_valid


def run_checks(project_root: Path) -> bool:
    print("==================================================")
    print(f"[*] Running Pre-Flight Verification on: {project_root}")
    print("==================================================")
    
    all_ok = True
    
    # 1. Structure check
    print("\n[1/4] Checking Required Files Structure...")
    struct_issues = check_structure(project_root)
    if struct_issues:
        for issue in struct_issues:
            if "WARNING" in issue:
                print(f"  [!] {issue}")
            else:
                print(f"  [X] {issue}")
                all_ok = False
    else:
        print("  [✓] Required structure passed.")

    # 2. Forbidden artifacts check
    print("\n[2/4] Scanning for Forbidden Artifacts (__pycache__, .venv, temp files)...")
    is_git_repo = (project_root / ".git").exists()
    artifact_issues = check_forbidden_artifacts(project_root, ignore_git=is_git_repo)
    if artifact_issues:
        for a in artifact_issues[:10]:
            print(f"  [X] {a}")
        if len(artifact_issues) > 10:
            print(f"  ... and {len(artifact_issues) - 10} more.")
        all_ok = False
    else:
        print("  [✓] No forbidden artifacts detected.")

    # 3. Prompt injection trap check
    print("\n[3/4] Scanning for AI Watermarking Trap ('mèo lượng tử')...")
    trap_issues = scan_for_trap_keywords(project_root)
    if trap_issues:
        for t in trap_issues:
            print(f"  [X] {t}")
        all_ok = False
    else:
        print("  [✓] Clean! No trap keywords detected in project source.")

    # 4. Total Size check
    print("\n[4/4] Verifying Package Size (< 20MB)...")
    total_bytes, size_ok = check_size(project_root)
    size_mb = total_bytes / (1024 * 1024)
    if size_ok:
        print(f"  [✓] Total Size: {size_mb:.2f} MB (within 20MB limit).")
    else:
        print(f"  [X] Total Size: {size_mb:.2f} MB (EXCEEDS 20MB limit! Must host on Google Drive).")
        all_ok = False

    print("\n==================================================")
    if all_ok:
        print(">>> RESULT: ALL CHECKS PASSED. Ready for packaging!")
    else:
        print(">>> RESULT: FAILED CHECKS. Please resolve the above issues.")
    print("==================================================")
    return all_ok


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    success = run_checks(target)
    sys.exit(0 if success else 1)
