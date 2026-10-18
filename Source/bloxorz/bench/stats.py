from dataclasses import dataclass, field
from typing import Any, List, Optional
import csv
import json

@dataclass
class Stats:
    """Standard statistics recorded during search."""
    expanded: int = 0
    generated: int = 0
    frontier_peak: int = 0
    time_s: float = 0.0
    peak_mem_bytes: int = 0

    @property
    def time_ms(self) -> float:
        return self.time_s * 1000.0

    @property
    def peak_mem_kb(self) -> float:
        return self.peak_mem_bytes / 1024.0

    @property
    def peak_mem_mb(self) -> float:
        return self.peak_mem_bytes / (1024.0 * 1024.0)

    def to_dict(self) -> dict:
        return {
            "expanded": self.expanded,
            "generated": self.generated,
            "frontier_peak": self.frontier_peak,
            "time_s": round(self.time_s, 4),
            "time_ms": round(self.time_ms, 2),
            "peak_mem_bytes": self.peak_mem_bytes,
            "peak_mem_kb": round(self.peak_mem_kb, 2),
            "peak_mem_mb": round(self.peak_mem_mb, 4),
        }


@dataclass
class SearchResult:
    """Standard result returned by any solver."""
    moves: Optional[List[Any]]  # None if no solution found
    cost: int
    stats: Stats


@dataclass
class BenchmarkRecord:
    """Record linking a stage, an algorithm, and its SearchResult."""
    algorithm: str
    stage_name: str
    group: str
    success: bool
    solution_length: int
    cost: int
    stats: Stats
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "algorithm": self.algorithm,
            "stage_name": self.stage_name,
            "group": self.group,
            "success": self.success,
            "solution_length": self.solution_length if self.success else -1,
            "cost": self.cost if self.success else -1,
            "error": self.error_message or ""
        }
        d.update(self.stats.to_dict())
        return d


def export_records_csv(records: List[BenchmarkRecord], filepath: str):
    """Saves benchmark records to CSV."""
    if not records:
        return
    fieldnames = [
        "algorithm", "stage_name", "group", "success", "solution_length",
        "cost", "time_s", "time_ms", "peak_mem_kb", "peak_mem_mb",
        "expanded", "generated", "frontier_peak", "error"
    ]
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())
    print(f"[✓] Exported CSV to: {filepath}")


def export_records_json(records: List[BenchmarkRecord], filepath: str):
    """Saves benchmark records to JSON."""
    data = [r.to_dict() for r in records]
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[✓] Exported JSON to: {filepath}")


def export_records_latex(
    records: List[BenchmarkRecord],
    filepath: Optional[str] = None,
    caption: str = "Bảng so sánh kết quả thực nghiệm 4 thuật toán tìm kiếm trên các nhóm màn chơi",
    label: str = "tab:benchmark_results"
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
        "\\textbf{Thuật toán} & \\textbf{Nhóm} & \\textbf{Màn chơi} & \\textbf{Thời gian (ms)} & \\textbf{RAM (KB)} & \\textbf{Số nút duyệt} & \\textbf{Số bước đi} \\\\",
        "\\midrule"
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
            f"{r.algorithm} & {r.group} & {r.stage_name} & {time_str} & {mem_str} & {nodes_str} & {moves_str} \\\\"
        )

    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}"
    ])
    table_code = "\n".join(lines)
    if filepath:
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(table_code)
        print(f"[✓] Exported LaTeX table to: {filepath}")
    return table_code
