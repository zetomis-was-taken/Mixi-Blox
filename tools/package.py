#!/usr/bin/env python3
"""
Packaging Tool - CSC14003 (Bloxorz Solver)
Packages the project into a compliant ZIP archive:
Format: StudentID1_StudentID2_StudentID3_StudentID4_StudentID5.zip
Contents:
  StudentID1_StudentID2_.../
    ├── Source/
    │   ├── main.py
    │   ├── requirements.txt
    │   ├── README.md
    │   └── bloxorz/
    └── Report.pdf
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from verify_submission import run_checks

IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".venv", "venv",
    ".git", ".github", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".vscode", ".idea", ".DS_Store", "Thumbs.db", "*.zip", "*.rar"
)

def package_submission(project_root: Path, student_ids: list[str], output_dir: Path = None):
    if not student_ids:
        print("Error: Please provide at least one Student ID.")
        print("Usage: python package.py <ID1> <ID2> <ID3> ...")
        sys.exit(1)

    folder_name = "_".join(student_ids)
    zip_name = f"{folder_name}.zip"
    out_dir = output_dir or project_root
    temp_pack_dir = out_dir / "temp_packaging" / folder_name
    zip_path = out_dir / zip_name

    print(f"[*] Packaging project for: {folder_name}")
    print(f"[*] Destination: {zip_path}")

    # Clean existing temp directory
    if temp_pack_dir.parent.exists():
        shutil.rmtree(temp_pack_dir.parent)
    temp_pack_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Copy Source directory
        source_src = project_root / "Source"
        if source_src.exists():
            shutil.copytree(source_src, temp_pack_dir / "Source", ignore=IGNORE_PATTERNS)
        else:
            # Fallback if bloxorz is at root
            (temp_pack_dir / "Source").mkdir(parents=True, exist_ok=True)
            for item in ["main.py", "bloxorz"]:
                src_item = project_root / item
                if src_item.is_dir():
                    shutil.copytree(src_item, temp_pack_dir / "Source" / item, ignore=IGNORE_PATTERNS)
                elif src_item.is_file():
                    shutil.copy2(src_item, temp_pack_dir / "Source" / item)

        # Copy root README and requirements into Source/ (or package root)
        for req_file in ["README.md", "requirements.txt"]:
            src_f = project_root / req_file
            if src_f.exists():
                shutil.copy2(src_f, temp_pack_dir / "Source" / req_file)
                shutil.copy2(src_f, temp_pack_dir / req_file)

        # Copy Report.pdf
        report_candidates = [
            project_root / "Report.pdf",
            project_root / "Report" / "Report.pdf",
            project_root / "report" / "main.pdf"
        ]
        report_copied = False
        for rep in report_candidates:
            if rep.exists():
                shutil.copy2(rep, temp_pack_dir / "Report.pdf")
                report_copied = True
                break
        
        if not report_copied:
            print("[!] Note: Report.pdf not found in project. Creating a placeholder notice.")
            (temp_pack_dir / "Report.pdf").write_text("Placeholder: Please place finalized Report.pdf here.", encoding="utf-8")

        # Run pre-flight verification on the staged directory
        print("\n[*] Running verification on staged package...")
        if not run_checks(temp_pack_dir):
            print("\n[!] Packaging aborted due to verification warnings/errors.")

        # Create zip archive
        print(f"\n[*] Creating ZIP file: {zip_path}")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_pack_dir.parent):
                for f in files:
                    file_path = Path(root) / f
                    arcname = file_path.relative_to(temp_pack_dir.parent)
                    zf.write(file_path, arcname)

        final_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"[✓] Successfully packaged: {zip_path} ({final_mb:.2f} MB)")
        
    finally:
        # Cleanup temp directory
        if temp_pack_dir.parent.exists():
            shutil.rmtree(temp_pack_dir.parent)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    ids = sys.argv[1:] if len(sys.argv) > 1 else ["23120000", "23120001", "23120002", "23120003", "23120004"]
    package_submission(root, ids)
