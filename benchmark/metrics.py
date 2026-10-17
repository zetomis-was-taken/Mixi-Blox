import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

@dataclass
class BenchmarkResult:
    """
    Data class storing the 4 essential metrics required by the assignment:
    1. search_time_seconds: Execution time of the search algorithm.
    2. peak_memory_kb: Maximum RAM used during search (in Kilobytes).
    3. expanded_nodes: Total number of states dequeued/expanded from Frontier.
    4. solution_length: Total number of moves in the found path.
    """
    algorithm: str
    level_name: str
    success: bool
    search_time_seconds: float
    peak_memory_kb: float
    expanded_nodes: int
    solution_length: int
    solution_path: List[Any] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def search_time_ms(self) -> float:
        """Returns search time in milliseconds."""
        return self.search_time_seconds * 1000.0

    @property
    def peak_memory_mb(self) -> float:
        """Returns peak memory in Megabytes."""
        return self.peak_memory_kb / 1024.0

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "level_name": self.level_name,
            "success": self.success,
            "search_time_ms": round(self.search_time_ms, 2),
            "search_time_s": round(self.search_time_seconds, 4),
            "peak_memory_kb": round(self.peak_memory_kb, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 4),
            "expanded_nodes": self.expanded_nodes,
            "solution_length": self.solution_length if self.success else -1,
            "error": self.error_message or ""
        }


def benchmark_search(
    solver_func: Callable[..., Any],
    algorithm_name: str,
    level_name: str,
    *args,
    **kwargs
) -> Tuple[Optional[Any], BenchmarkResult]:
    """
    Executes a search algorithm with memory tracing and high-precision timer.
    
    The solver_func is expected to return either:
        (solution_path, expanded_nodes)
    OR an object with attributes:
        `path` (or `moves`), and `expanded_nodes` (or `nodes_expanded`).
    """
    # Start memory tracing
    tracemalloc.start()
    tracemalloc.reset_peak()
    
    start_time = time.perf_counter()
    raw_result = None
    success = False
    error_msg = None
    expanded_nodes = 0
    solution_path = []

    try:
        raw_result = solver_func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Parse return values
        if isinstance(raw_result, tuple):
            if len(raw_result) >= 2:
                solution_path, expanded_nodes = raw_result[0], raw_result[1]
            elif len(raw_result) == 1:
                solution_path = raw_result[0]
        elif hasattr(raw_result, "path") and hasattr(raw_result, "expanded_nodes"):
            solution_path = raw_result.path
            expanded_nodes = raw_result.expanded_nodes
        elif isinstance(raw_result, list):
            solution_path = raw_result

        success = solution_path is not None and len(solution_path) > 0
    except Exception as exc:
        end_time = time.perf_counter()
        error_msg = str(exc)
        success = False
    finally:
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    search_time = end_time - start_time
    peak_memory_kb = peak_memory / 1024.0
    solution_length = len(solution_path) if success and solution_path else 0

    result = BenchmarkResult(
        algorithm=algorithm_name,
        level_name=level_name,
        success=success,
        search_time_seconds=search_time,
        peak_memory_kb=peak_memory_kb,
        expanded_nodes=expanded_nodes,
        solution_length=solution_length,
        solution_path=solution_path if success else [],
        error_message=error_msg
    )

    return raw_result, result
