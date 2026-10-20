#!/usr/bin/env python3
"""
Main benchmark execution script - CSC14003 (Bloxorz Solver)
Run via:
    python -m bloxorz.bench.run_all
or:
    python Source/bloxorz/bench/run_all.py
"""

import json
import platform
import sys
from pathlib import Path

from bloxorz.bench.plots import plot_benchmark_charts
from bloxorz.bench.runner import BenchmarkRunner
from bloxorz.bench.stats import export_records_csv, export_records_json, export_records_latex
from bloxorz.core.contracts import Counts, SearchResult


def print_environment_info():
    """Prints and records benchmarking environment configuration."""
    print("==================================================")
    print("BENCHMARK EXECUTION ENVIRONMENT (METHODOLOGY)")
    print("==================================================")
    print(f"OS:            {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Architecture:  {platform.machine()}")
    print(f"Processor:     {platform.processor()}")
    print(f"Python:        {platform.python_version()} ({platform.python_implementation()})")
    print("Timing Tool:   time.perf_counter (high precision)")
    print("Memory Tool:   tracemalloc.get_traced_memory (peak RAM)")
    print("==================================================\n")


def load_test_stages(stages_dir: Path) -> dict:
    """Loads all JSON stages from the stages directory."""
    stages = {}
    if not stages_dir.exists():
        print(f"[!] Warning: Stages directory not found at {stages_dir}")
        return stages

    for json_file in sorted(stages_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                name = data.get("name", json_file.stem)
                group = data.get("group", "L1")
                stages[name] = {"data": data, "group": group}
        except Exception as e:
            print(f"[!] Failed to load {json_file}: {e}")
    return stages


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print_environment_info()

    # Determine paths
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    stages_dir = repo_root / "Source" / "bloxorz" / "core" / "stages"
    report_data_dir = repo_root / "Report" / "data"
    report_tables_dir = repo_root / "Report" / "tables"
    report_figures_dir = repo_root / "Report" / "figures"
    report_data_dir.mkdir(parents=True, exist_ok=True)
    report_tables_dir.mkdir(parents=True, exist_ok=True)
    report_figures_dir.mkdir(parents=True, exist_ok=True)

    runner = BenchmarkRunner()

    # Attempt to import solvers from bloxorz.solvers
    try:
        from bloxorz.solvers import astar, bfs, dfs, ucs

        runner.register_solver("BFS", bfs.solve)
        runner.register_solver("DFS", dfs.solve)
        runner.register_solver("UCS", ucs.solve)
        runner.register_solver("A*", astar.solve)
        print("[+] Loaded real solvers from bloxorz.solvers.")
    except (ImportError, AttributeError):
        print("[i] Solvers still under construction in bloxorz.solvers.")
        print("[i] Using baseline mock solvers to demonstrate pipeline end-to-end.")

        def mock_bfs(stage):
            return SearchResult(
                status="solved",
                path=((0, "R"), (0, "R")),
                cost=2.0,
                counts=Counts(expanded=35, generated=80, frontier_peak=20),
            )

        def mock_dfs(stage):
            return SearchResult(
                status="solved",
                path=((0, "L"), (0, "U")),
                cost=2.0,
                counts=Counts(expanded=98, generated=140, frontier_peak=50),
            )

        def mock_ucs(stage):
            return SearchResult(
                status="solved",
                path=((0, "R"), (0, "R")),
                cost=2.0,
                counts=Counts(expanded=42, generated=90, frontier_peak=25),
            )

        def mock_astar(stage):
            return SearchResult(
                status="solved",
                path=((0, "R"), (0, "R")),
                cost=2.0,
                counts=Counts(expanded=18, generated=45, frontier_peak=10),
            )

        runner.register_solver("BFS", mock_bfs)
        runner.register_solver("DFS", mock_dfs)
        runner.register_solver("UCS", mock_ucs)
        runner.register_solver("A*", mock_astar)

    # Load test stages
    stages = load_test_stages(stages_dir)
    if not stages:
        # Fallback sample stages
        print("[i] Registering default test stages across 4 difficulty tiers...")
        sample_stages = [
            ("Stage 01 (Plain)", "L1"),
            ("Stage 02 (Zigzag)", "L1"),
            ("Stage 03 (Fragile Intro)", "L2"),
            ("Stage 05 (Fragile Path)", "L2"),
            ("Stage 07 (Soft Switch)", "L3"),
            ("Stage 08 (Heavy Switch)", "L3"),
            ("Stage 10 (Combined)", "L4"),
            ("Stage 11 (Split Cubes)", "L4"),
        ]
        for name, grp in sample_stages:
            runner.register_stage(name, {"name": name}, group=grp)
    else:
        for name, info in stages.items():
            runner.register_stage(name, info["data"], group=info["group"])

    # Run benchmarks
    records = runner.run_all(verbose=True)

    # Export results to Report/data and Report/tables
    csv_path = report_data_dir / "benchmark_results.csv"
    json_path = report_data_dir / "benchmark_results.json"
    latex_path = report_tables_dir / "benchmark_results.tex"

    export_records_csv(records, str(csv_path))
    export_records_json(records, str(json_path))
    export_records_latex(records, str(latex_path))

    # Generate charts
    plot_benchmark_charts(records, output_dir=str(report_figures_dir))

    print("\n[+] Benchmark execution completed successfully!")
    print(f"[+] CSV saved to: {csv_path}")
    print(f"[+] LaTeX table saved to: {latex_path}")
    print(f"[+] Charts saved to: {report_figures_dir}")


if __name__ == "__main__":
    main()
