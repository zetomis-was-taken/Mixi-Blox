import gc
import sys
import time
import tracemalloc
from typing import Any, Callable, Dict, List, Optional
from .stats import BenchmarkRecord, SearchResult, Stats

class BenchmarkRunner:
    """
    Orchestrates execution of Bloxorz search algorithms across test stages.
    Accurately measures time.perf_counter and peak memory via tracemalloc.
    """

    def __init__(self):
        self.solvers: Dict[str, Callable[[Any], SearchResult]] = {}
        self.stages: Dict[str, Dict[str, Any]] = {}
        self.records: List[BenchmarkRecord] = []

    def register_solver(self, name: str, solver_fn: Callable[[Any], SearchResult]):
        """Registers a solver function: solver_fn(stage_data) -> SearchResult."""
        self.solvers[name] = solver_fn

    def register_stage(self, name: str, stage_data: Any, group: str = "L1"):
        """Registers a stage along with its difficulty group (L1, L2, L3, L4)."""
        self.stages[name] = {"data": stage_data, "group": group}

    def run_single(self, algo_name: str, stage_name: str, stage_data: Any, group: str, runs: int = 3) -> BenchmarkRecord:
        """Runs a solver across multiple runs (median of 3 per Issue #30) with isolated resource tracking."""
        solver_fn = self.solvers[algo_name]

        times: List[float] = []
        memories: List[int] = []
        raw_result: Optional[SearchResult] = None
        error_msg: Optional[str] = None
        success = False

        for _ in range(max(1, runs)):
            gc.collect()
            tracemalloc.start()
            tracemalloc.reset_peak()
            start_time = time.perf_counter()

            try:
                current_result = solver_fn(stage_data)
                end_time = time.perf_counter()
                _, peak_bytes = tracemalloc.get_traced_memory()
                times.append(end_time - start_time)
                memories.append(peak_bytes)
                raw_result = current_result
                status = getattr(raw_result, "status", "solved") if raw_result is not None else "unsolvable"
                success = (raw_result is not None) and (status == "solved")
            except Exception as exc:
                end_time = time.perf_counter()
                _, peak_bytes = tracemalloc.get_traced_memory()
                error_msg = str(exc)
                success = False
                break
            finally:
                tracemalloc.stop()

        if not times:
            elapsed_seconds = 0.0
            peak_bytes = 0
        else:
            times.sort()
            memories.sort()
            mid = len(times) // 2
            elapsed_seconds = times[mid]
            peak_bytes = memories[mid]

        # Merge measurements
        if raw_result and hasattr(raw_result, "stats"):
            solver_stats = raw_result.stats
            solver_stats.time_s = elapsed_seconds
            solver_stats.peak_mem_bytes = peak_bytes
            path = getattr(raw_result, "path", getattr(raw_result, "moves", None))
            moves = len(path) if path is not None else -1
            cost = getattr(raw_result, "cost", moves)
        else:
            solver_stats = Stats(
                expanded=0,
                time_s=elapsed_seconds,
                peak_mem_bytes=peak_bytes
            )
            moves = -1
            cost = -1

        return BenchmarkRecord(
            algorithm=algo_name,
            stage_name=stage_name,
            group=group,
            success=success,
            solution_length=moves,
            cost=cost,
            stats=solver_stats,
            error_message=error_msg
        )

    def run_all(self, verbose: bool = True) -> List[BenchmarkRecord]:
        """Runs all registered solvers on all registered stages."""
        self.records.clear()
        
        for stage_name, info in self.stages.items():
            stage_data = info["data"]
            group = info["group"]
            if verbose:
                print(f"\n==========================================")
                print(f">> Stage: {stage_name} [{group}]")
                print(f"==========================================")

            for algo_name in self.solvers:
                if verbose:
                    print(f"  Running [{algo_name}]...", end=" ", flush=True)

                record = self.run_single(algo_name, stage_name, stage_data, group)
                self.records.append(record)

                if verbose:
                    if record.success:
                        print(f"OK | Time: {record.stats.time_ms:.1f}ms | RAM: {record.stats.peak_mem_kb:.1f}KB | Nodes: {record.stats.expanded} | Moves: {record.solution_length}")
                    else:
                        print(f"FAILED | {record.error_message or 'No solution'}")

        return self.records
