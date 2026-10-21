import csv
import json
from dataclasses import dataclass
from typing import List, Optional

from bloxorz.core.contracts import SearchResult, Stats

__all__ = [
    "SearchResult",
    "Stats",
    "BenchmarkRecord",
    "stats_to_dict",
    "export_records_csv",
    "export_records_json",
    "export_records_latex",
]


def stats_to_dict(stats: Stats) -> dict:
    """Converts a frozen Stats object to a dictionary for serialization."""
    return {
        "expanded": stats.expanded,
        "generated": stats.generated,
        "frontier_peak": stats.frontier_peak,
        "time_s": round(stats.time_s, 4),
        "time_ms": round(stats.time_ms, 2),
        "peak_mem_bytes": stats.peak_mem_bytes,
        "peak_mem_kb": round(stats.peak_mem_kb, 2),
        "peak_mem_mb": round(stats.peak_mem_mb, 4),
    }


@dataclass
class BenchmarkRecord:
    """
    Record linking a stage, an algorithm, and its SearchResult.

    Note on schema design (contracts.md § Stats):
    The harness decorates the core SearchResult with benchmarking execution metadata
    (algorithm name, stage name, stage group). It derives `success: bool` from
    (status == "solved") and `solution_length: int` (len(path) when solved, -1 otherwise)
    for reporting and tabular ease, while preserving `cost: float` to match
    step_cost and SearchResult.cost without truncation.
    """

    algorithm: str
    stage_name: str
    group: str
    success: bool
    solution_length: int
    cost: float
    stats: Stats
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "algorithm": self.algorithm,
            "stage_name": self.stage_name,
            "group": self.group,
            "success": self.success,
            "solution_length": self.solution_length if self.success else -1,
            "cost": round(self.cost, 2) if self.success and self.cost >= 0 else -1.0,
            "error": self.error_message or "",
        }
        d.update(stats_to_dict(self.stats))
        return d


def export_records_csv(records: List[BenchmarkRecord], filepath: str):
    """Saves benchmark records to CSV."""
    if not records:
        return
    fieldnames = [
        "algorithm",
        "stage_name",
        "group",
        "success",
        "solution_length",
        "cost",
        "time_s",
        "time_ms",
        "peak_mem_kb",
        "peak_mem_mb",
        "expanded",
        "generated",
        "frontier_peak",
        "error",
    ]
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())
    print(f"[+] Exported CSV to: {filepath}")


def export_records_json(records: List[BenchmarkRecord], filepath: str):
    """Saves benchmark records to JSON."""
    data = [r.to_dict() for r in records]
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[+] Exported JSON to: {filepath}")


def export_records_latex(
    records: List[BenchmarkRecord],
    filepath: Optional[str] = None,
    caption: str = "Bảng so sánh kết quả thực nghiệm 4 thuật toán tìm kiếm trên các nhóm màn chơi",
    label: str = "tab:benchmark_results",
) -> str:
    """Generates standard LaTeX booktabs table for the report."""
    lines = [
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\small",
        "\\begin{tabular}{lllcccc}",
        "\\toprule",
        "\\textbf{Thuật toán} & \\textbf{Nhóm} & \\textbf{Màn chơi} & "
        "\\textbf{Thời gian (ms)} & \\textbf{RAM (KB)} & "
        "\\textbf{Số nút duyệt} & \\textbf{Số bước đi} \\\\",
        "\\midrule",
    ]

    current_group = None
    for r in records:
        if current_group is not None and current_group != r.group:
            lines.append("\\midrule")
        current_group = r.group

        time_str = f"{r.stats.time_ms:.2f}" if r.success else "-"
        mem_str = f"{r.stats.peak_mem_kb:.2f}" if r.success else "-"
        nodes_str = f"{r.stats.expanded:,}" if r.success else "-"
        moves_str = f"{r.solution_length}" if r.success else "-"

        lines.append(
            f"{r.algorithm} & {r.group} & {r.stage_name} & "
            f"{time_str} & {mem_str} & {nodes_str} & {moves_str} \\\\"
        )

    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
    table_code = "\n".join(lines)
    if filepath:
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(table_code)
        print(f"[+] Exported LaTeX table to: {filepath}")
    return table_code
