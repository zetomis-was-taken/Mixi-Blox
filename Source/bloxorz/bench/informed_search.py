"""Reproducible solver handoff measurements, separate from the #24 harness.

Run from the repository root with Source on PYTHONPATH:
    python -m bloxorz.bench.informed_search
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import platform
import statistics
import subprocess
import tracemalloc
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable

from bloxorz.core.contracts import Caps, SearchResult, Stage, Stats
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import astar, bfs, dfs, ucs

ROOT = Path(__file__).resolve().parents[3]
SOLVERS = {"BFS": bfs.solve, "DFS": dfs.solve, "UCS": ucs.solve, "A*": astar.solve}


def measure(solver: Callable[[Stage, Caps], SearchResult], stage: Stage, caps: Caps) -> dict:
    """Three isolated calls, exact result/count agreement, medians of time and heap peak."""
    results, times, memories = [], [], []
    for _ in range(3):
        gc.collect()
        tracemalloc.start()
        tracemalloc.reset_peak()
        try:
            started = perf_counter()
            result = solver(stage, caps)
            elapsed = perf_counter() - started
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        results.append(result)
        times.append(elapsed)
        memories.append(peak)
    if any(result != results[0] for result in results[1:]):
        raise AssertionError("search outcome, path or counts differed across repetitions")
    result = results[0]
    if result.status == "solved":
        board, state, cost = Board(stage), Board(stage).start(), 0.0
        for action in result.path:
            child = {a: s for s, a in board.successors(state)}[action]
            cost += board.step_cost(state, action, child)
            state = child
        if not board.is_goal(state) or cost != result.cost:
            raise AssertionError("solver path did not replay to the claimed goal and cost")
    stats = Stats(
        result.counts.expanded,
        result.counts.generated,
        result.counts.frontier_peak,
        statistics.median(times),
        int(statistics.median(memories)),
    )
    return {
        "status": result.status,
        "moves": len(result.path) if result.status == "solved" else None,
        "cost": result.cost if result.status == "solved" else None,
        **asdict(stats),
        "time_ms": stats.time_ms,
        "peak_mem_kb": stats.peak_mem_kb,
        "raw_time_s": times,
        "raw_peak_mem_bytes": memories,
        "error_message": None,
    }


def source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "Source").rglob("*")):
        if path.suffix in (".py", ".json"):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def markdown(records: list[dict], metadata: dict) -> str:
    lines = [
        "# Kết quả đo UCS/A* và các adapter đối chứng",
        "",
        "Kết quả thực đo trên máy cục bộ, trung vị của ba lần chạy độc lập mỗi cặp.",
        "BFS/DFS ở đây là các adapter mỏng của vòng lặp chung #18; số liệu chưa thay thế",
        "bảng thí nghiệm toàn nhóm do harness #24 quản lý.",
        "",
        f"- Thời điểm UTC: `{metadata['created_at_utc']}`.",
        f"- Python: `{metadata['python']}`; nền tảng: `{metadata['platform']}`.",
        f"- Commit nền: `{metadata['base_commit']}`.",
        f"- SHA-256 mã và màn chơi: `{metadata['source_sha256']}`.",
        "- Cost: 1 + số ô dễ vỡ mới tiếp xúc trong hành động.",
        "- Time chỉ đo lời gọi `solve(stage, caps)`; không gồm load, replay, I/O hay vẽ hình.",
        "- Bộ nhớ là peak heap Python do `tracemalloc` ghi nhận, không phải RAM toàn tiến trình.",
        "- Ba lần chạy phải trùng kết quả, đường đi, chi phí và bộ đếm; "
        "không lấy trung bình bộ đếm.",
        "",
        "| Màn | Thuật toán | Kết quả | Bước | Chi phí | Mở rộng | Sinh ra | "
        "Đỉnh hàng đợi | ms | KiB |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in records:

        def value(key: str) -> str:
            v = row.get(key)
            return "-" if v is None else str(v)

        status = {
            "solved": "GIẢI ĐƯỢC",
            "cap": "ĐẠT GIỚI HẠN",
            "unsolvable": "KHÔNG CÓ NGHIỆM",
            "error": "LỖI",
        }[row["status"]]
        lines.append(
            f"| {row['stage']} | {row['algorithm']} | {status} | {value('moves')} | "
            f"{value('cost')} | {value('expanded')} | {value('generated')} | "
            f"{value('frontier_peak')} | "
            + (f"{row['time_ms']:.2f}" if row.get("time_ms") is not None else "-")
            + " | "
            + (f"{row['peak_mem_kb']:.2f}" if row.get("peak_mem_kb") is not None else "-")
            + " |"
        )
    return "\n".join(lines) + "\n"


def plot(records: list[dict], directory: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory.mkdir(parents=True, exist_ok=True)
    stages = list(dict.fromkeys(row["stage"] for row in records))
    metrics = {
        "time_ms": ("Thời gian tìm kiếm", "Trung vị (ms)"),
        "peak_mem_kb": ("Bộ nhớ heap đỉnh", "Trung vị (KiB)"),
        "expanded": ("Số nút mở rộng", "Nút"),
        "moves": ("Độ dài lời giải", "Bước"),
        "cost": ("Tổng chi phí lời giải", "Chi phí"),
    }
    for metric, (title, label) in metrics.items():
        fig, ax = plt.subplots(figsize=(12, 4.8), layout="constrained")
        for index, algorithm in enumerate(SOLVERS):
            selected = {row["stage"]: row for row in records if row["algorithm"] == algorithm}
            values = [
                float(selected[stage][metric])
                if selected[stage].get(metric) is not None
                else float("nan")
                for stage in stages
            ]
            ax.bar(
                [i + (index - 1.5) * 0.2 for i in range(len(stages))],
                values,
                width=0.2,
                label=algorithm,
            )
        ax.set(title=title, ylabel=label, xlabel="Màn chơi")
        ax.set_xticks(range(len(stages)), stages, rotation=30)
        ax.legend(ncols=4)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        for suffix in ("png", "svg"):
            fig.savefig(directory / f"{metric}.{suffix}", dpi=180)
        plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "Report/data/informed_search")
    parser.add_argument("--figures", type=Path, default=ROOT / "Report/figures/informed_search")
    parser.add_argument(
        "--markdown", type=Path, help="also write the measured Vietnamese table here"
    )
    args = parser.parse_args(argv)
    # Loading/validation/index compilation is deliberately outside all measured windows.
    stages = [
        load_stage(path) for path in sorted((ROOT / "Source/bloxorz/core/stages").glob("*.json"))
    ]
    if len(stages) < 10:
        parser.error("at least ten committed stages are required")
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": source_digest(ROOT),
        "repetitions": 3,
        "node_cap": 100_000,
        "time_cap_s": None,
    }
    records = []
    for stage in stages:
        for algorithm, solver in SOLVERS.items():
            try:
                row = measure(solver, stage, Caps(node_cap=100_000))
            except Exception as exc:
                row = {"status": "error", "error_message": f"{type(exc).__name__}: {exc}"}
            row.update(stage=stage.id, group=stage.group, algorithm=algorithm)
            records.append(row)
            print(f"{stage.id} {algorithm}: {row['status']}")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "results.json").write_text(
        json.dumps({"metadata": metadata, "records": records}, indent=2), encoding="utf-8"
    )
    fields = [
        "stage",
        "group",
        "algorithm",
        "status",
        "moves",
        "cost",
        "expanded",
        "generated",
        "frontier_peak",
        "time_s",
        "peak_mem_bytes",
        "error_message",
    ]
    with (args.output / "results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow(
                {key: row.get(key) if row.get(key) is not None else "-" for key in fields}
            )
    text = markdown(records, metadata)
    (args.output / "results_vi.md").write_text(text, encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(text, encoding="utf-8")
    plot(records, args.figures)
    return 1 if any(row["status"] != "solved" for row in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
