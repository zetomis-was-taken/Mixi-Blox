import os
from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
from .metrics import BenchmarkResult

def plot_benchmark_results(
    results: List[BenchmarkResult],
    output_dir: str = "report/figures",
    filename_prefix: str = "benchmark"
):
    """
    Generates 4 publication-ready comparison bar charts for the LaTeX report:
    1. Search Time (ms)
    2. Peak Memory (KB)
    3. Expanded Nodes
    4. Solution Length (number of steps)
    
    Saves in both PNG (for preview) and PDF (for crisp LaTeX vector graphics).
    """
    if not results:
        print("No benchmark results to plot.")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Filter successful runs
    valid_results = [r for r in results if r.success]
    if not valid_results:
        print("No successful results found to plot.")
        return

    # Extract distinct levels and algorithms
    levels = list(dict.fromkeys(r.level_name for r in valid_results))
    algorithms = list(dict.fromkeys(r.algorithm for r in valid_results))

    # Predefined harmonious colors for algorithms
    palette = {
        "BFS": "#1f77b4",     # Muted Blue
        "DFS": "#ff7f0e",     # Orange
        "IDS": "#d62728",     # Red
        "UCS": "#2ca02c",     # Green
        "A*": "#9467bd",      # Purple
        "A* (Heuristic 1)": "#9467bd",
        "A* (Heuristic 2)": "#8c564b"
    }

    metrics_to_plot = [
        ("search_time_ms", "Thời gian tìm kiếm (ms)", f"{filename_prefix}_search_time", True),
        ("peak_memory_kb", "Bộ nhớ RAM đỉnh (KB)", f"{filename_prefix}_peak_memory", True),
        ("expanded_nodes", "Số nút đã mở rộng (Expanded Nodes)", f"{filename_prefix}_expanded_nodes", True),
        ("solution_length", "Độ dài lời giải (Số bước đi)", f"{filename_prefix}_solution_length", False)
    ]

    x = np.arange(len(levels))
    bar_width = 0.8 / max(len(algorithms), 1)

    for metric_attr, y_label, file_name, log_scale in metrics_to_plot:
        fig, ax = plt.subplots(figsize=(9, 5), dpi=300)

        for i, algo in enumerate(algorithms):
            values = []
            for lvl in levels:
                matched = [getattr(r, metric_attr) for r in valid_results if r.algorithm == algo and r.level_name == lvl]
                values.append(matched[0] if matched else 0)

            offset = (i - len(algorithms) / 2 + 0.5) * bar_width
            color = palette.get(algo, plt.cm.tab10(i % 10))
            bars = ax.bar(x + offset, values, bar_width, label=algo, color=color, edgecolor="black", linewidth=0.6, alpha=0.9)

        ax.set_xlabel("Màn chơi (Test Levels)", fontsize=11, fontweight="bold", labelpad=8)
        ax.set_ylabel(y_label, fontsize=11, fontweight="bold", labelpad=8)
        ax.set_title(f"So sánh {y_label} giữa các thuật toán", fontsize=13, fontweight="bold", pad=12)
        ax.set_xticks(x)
        ax.set_xticklabels(levels, fontsize=10, rotation=15 if len(levels) > 4 else 0)
        ax.legend(title="Thuật toán", fontsize=9, title_fontsize=10, framealpha=0.9)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        # Set log scale if values span multiple orders of magnitude
        if log_scale:
            # Check max value
            all_vals = [getattr(r, metric_attr) for r in valid_results if getattr(r, metric_attr) > 0]
            if all_vals and max(all_vals) / (min(all_vals) + 1e-6) > 50:
                ax.set_yscale("log")
                ax.set_ylabel(f"{y_label} (Log scale)", fontsize=11, fontweight="bold")

        fig.tight_layout()

        # Save both PNG and PDF
        png_path = os.path.join(output_dir, f"{file_name}.png")
        pdf_path = os.path.join(output_dir, f"{file_name}.pdf")
        fig.savefig(png_path)
        fig.savefig(pdf_path)
        plt.close(fig)
        print(f"Generated plot: {png_path} & {pdf_path}")
