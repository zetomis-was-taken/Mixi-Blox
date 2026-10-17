import csv
import json
from typing import Any, Callable, Dict, List, Optional
from .metrics import BenchmarkResult, benchmark_search

class BenchmarkRunner:
    """
    Manages benchmarking multiple search algorithms across a suite of levels/stages.
    Supports exporting to CSV, JSON, Markdown, and LaTeX table formats.
    """

    def __init__(self):
        self.algorithms: Dict[str, Callable[..., Any]] = {}
        self.levels: Dict[str, Any] = {}
        self.results: List[BenchmarkResult] = []

    def register_algorithm(self, name: str, solver_func: Callable[..., Any]):
        """Registers a search algorithm (e.g. 'BFS', 'DFS', 'UCS', 'A*')."""
        self.algorithms[name] = solver_func

    def register_level(self, name: str, level_data: Any):
        """Registers a level instance or level configuration."""
        self.levels[name] = level_data

    def run_all(self, verbose: bool = True) -> List[BenchmarkResult]:
        """Runs all registered algorithms on all registered levels."""
        self.results.clear()
        
        for lvl_name, lvl_data in self.levels.items():
            if verbose:
                print(f"\n==========================================")
                print(f">> Testing Level: {lvl_name}")
                print(f"==========================================")
            
            for algo_name, solver_func in self.algorithms.items():
                if verbose:
                    print(f"  Running [{algo_name}]...", end=" ", flush=True)
                
                _, result = benchmark_search(
                    solver_func=solver_func,
                    algorithm_name=algo_name,
                    level_name=lvl_name,
                    level_data=lvl_data
                )
                self.results.append(result)
                
                if verbose:
                    if result.success:
                        print(f"SUCCESS | Time: {result.search_time_ms:.1f}ms | RAM: {result.peak_memory_kb:.1f}KB | Nodes: {result.expanded_nodes} | Moves: {result.solution_length}")
                    else:
                        print(f"FAILED! Error: {result.error_message}")
        
        return self.results

    def export_csv(self, filepath: str):
        """Exports benchmark results to a CSV file."""
        if not self.results:
            print("No results to export.")
            return

        fieldnames = [
            "algorithm", "level_name", "success", "search_time_ms", 
            "search_time_s", "peak_memory_kb", "peak_memory_mb", 
            "expanded_nodes", "solution_length", "error"
        ]

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.results:
                writer.writerow(r.to_dict())
        print(f"Saved benchmark CSV to {filepath}")

    def export_json(self, filepath: str):
        """Exports benchmark results to a JSON file."""
        data = [r.to_dict() for r in self.results]
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved benchmark JSON to {filepath}")

    def to_markdown_table(self) -> str:
        """Renders results as a GitHub Markdown table."""
        lines = [
            "| Algorithm | Level | Status | Time (ms) | Peak RAM (KB) | Expanded Nodes | Solution Length |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
        ]
        for r in self.results:
            status = "OK" if r.success else "FAIL"
            lines.append(
                f"| {r.algorithm} | {r.level_name} | {status} | "
                f"{r.search_time_ms:.2f} | {r.peak_memory_kb:.2f} | "
                f"{r.expanded_nodes} | {r.solution_length} |"
            )
        return "\n".join(lines)

    def to_latex_table(self, caption: str = "Bảng so sánh kết quả thực nghiệm giữa các thuật toán", label: str = "tab:benchmark_results") -> str:
        """
        Generates standard LaTeX booktabs table code ready to paste into the report.
        """
        lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            "\\begin{tabular}{llcccc}",
            "\\toprule",
            "\\textbf{Thuật toán} & \\textbf{Màn chơi} & \\textbf{Thời gian (ms)} & \\textbf{Bộ nhớ (KB)} & \\textbf{Số nút duyệt} & \\textbf{Độ dài bước đi} \\\\",
            "\\midrule"
        ]

        current_level = None
        for r in self.results:
            if current_level is not None and current_level != r.level_name:
                lines.append("\\midrule")
            current_level = r.level_name

            time_str = f"{r.search_time_ms:.2f}" if r.success else "-"
            mem_str = f"{r.peak_memory_kb:.2f}" if r.success else "-"
            nodes_str = f"{r.expanded_nodes:,}" if r.success else "-"
            len_str = f"{r.solution_length}" if r.success else "-"

            lines.append(
                f"{r.algorithm} & {r.level_name} & {time_str} & {mem_str} & {nodes_str} & {len_str} \\\\"
            )

        lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}"
        ])
        return "\n".join(lines)

    def export_latex_table(self, filepath: str, caption: str = "Bảng so sánh kết quả thực nghiệm giữa các thuật toán", label: str = "tab:benchmark_results"):
        """Exports the LaTeX table directly to a .tex file."""
        content = self.to_latex_table(caption=caption, label=label)
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved LaTeX table to {filepath}")

