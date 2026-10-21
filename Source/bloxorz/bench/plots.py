import os
from typing import List

try:
    import matplotlib.pyplot as plt
    import numpy as np

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .stats import BenchmarkRecord

PALETTE = {
    "BFS": "#1f77b4",  # Blue
    "DFS": "#ff7f0e",  # Orange
    "IDS": "#d62728",  # Red
    "UCS": "#2ca02c",  # Green
    "A*": "#9467bd",  # Purple
    "A* (h1)": "#9467bd",
    "A* (h2)": "#8c564b",
}


def plot_benchmark_charts(
    records: List[BenchmarkRecord],
    output_dir: str = "Report/figures",
    filename_prefix: str = "benchmark",
):
    """
    Plots the 4 required comparison charts and exports them as PNG and PDF:
    1. Search Time (ms)
    2. Peak Memory (KB)
    3. Expanded Nodes
    4. Solution Length (Moves)
    """
    if not HAS_MATPLOTLIB:
        print("[!] Note: matplotlib and numpy are not installed. Skipping plot chart generation.")
        return

    if not records:
        print("[!] No records to plot.")
        return

    os.makedirs(output_dir, exist_ok=True)
    valid_records = [r for r in records if r.success]
    if not valid_records:
        print("[!] No successful records found to plot.")
        return

    stages = list(dict.fromkeys(r.stage_name for r in valid_records))
    algorithms = list(dict.fromkeys(r.algorithm for r in valid_records))

    metrics = [
        ("time_ms", "Thời gian tìm kiếm (ms)", f"{filename_prefix}_time", True),
        ("peak_mem_kb", "Bộ nhớ RAM đỉnh (KB)", f"{filename_prefix}_memory", True),
        ("expanded", "Số nút đã mở rộng (Expanded Nodes)", f"{filename_prefix}_nodes", True),
        ("solution_length", "Độ dài lời giải (Số bước đi)", f"{filename_prefix}_moves", False),
    ]

    x = np.arange(len(stages))
    bar_width = 0.8 / max(len(algorithms), 1)

    for metric_key, y_label, file_name, log_scale in metrics:
        fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

        for i, algo in enumerate(algorithms):
            values = []
            for stg in stages:
                matched = [
                    getattr(r.stats, metric_key)
                    if hasattr(r.stats, metric_key)
                    else getattr(r, metric_key)
                    for r in valid_records
                    if r.algorithm == algo and r.stage_name == stg
                ]
                values.append(matched[0] if matched else 0)

            offset = (i - len(algorithms) / 2 + 0.5) * bar_width
            color = PALETTE.get(algo, plt.cm.tab10(i % 10))
            ax.bar(
                x + offset,
                values,
                bar_width,
                label=algo,
                color=color,
                edgecolor="black",
                linewidth=0.6,
                alpha=0.9,
            )

        ax.set_xlabel("Màn chơi kiểm thử (Test Stages)", fontsize=11, fontweight="bold", labelpad=8)
        ax.set_ylabel(y_label, fontsize=11, fontweight="bold", labelpad=8)
        ax.set_title(
            f"So sánh {y_label} giữa các thuật toán", fontsize=13, fontweight="bold", pad=12
        )
        ax.set_xticks(x)
        ax.set_xticklabels(stages, fontsize=9, rotation=20 if len(stages) > 4 else 0)
        ax.legend(title="Thuật toán", fontsize=9, title_fontsize=10, framealpha=0.9)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        if log_scale:
            all_vals = []
            for r in valid_records:
                v = (
                    getattr(r.stats, metric_key)
                    if hasattr(r.stats, metric_key)
                    else getattr(r, metric_key)
                )
                if v > 0:
                    all_vals.append(v)
            if all_vals and max(all_vals) / (min(all_vals) + 1e-6) > 50:
                ax.set_yscale("log")
                ax.set_ylabel(f"{y_label} (Log scale)", fontsize=11, fontweight="bold")

        fig.tight_layout()
        png_path = os.path.join(output_dir, f"{file_name}.png")
        pdf_path = os.path.join(output_dir, f"{file_name}.pdf")
        fig.savefig(png_path)
        fig.savefig(pdf_path)
        plt.close(fig)
        print(f"[✓] Saved chart: {png_path} & {pdf_path}")
