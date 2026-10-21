#!/usr/bin/env python3
"""
Main benchmark execution script - CSC14003 (Bloxorz Solver)
Run via:
    python -m bloxorz.bench.run_all
or:
    python Source/bloxorz/bench/run_all.py
"""

import platform
import sys
from pathlib import Path

from bloxorz.bench.plots import plot_benchmark_charts
from bloxorz.bench.runner import BenchmarkRunner
from bloxorz.bench.stats import export_records_csv, export_records_json, export_records_latex
from bloxorz.core.stage import load_stage


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
    """Loads all JSON stages from the stages directory via frozen load_stage."""
    stages = {}
    if not stages_dir.exists():
        print(f"[!] Warning: Stages directory not found at {stages_dir}")
        return stages

    for json_file in sorted(stages_dir.glob("*.json")):
        try:
            stage = load_stage(json_file)
            stages[stage.name] = {"data": stage, "group": stage.group}
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
    except (ImportError, AttributeError) as exc:
        print(f"[!] Solvers are not yet implemented in bloxorz.solvers: {exc}")
        print("[!] Dropped mock solver fallbacks per Issue #37. Exiting without fake data.")
        return

    # Load test stages
    stages = load_test_stages(stages_dir)
    if not stages:
        print(f"[!] No stages loaded from {stages_dir}")
        return

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
