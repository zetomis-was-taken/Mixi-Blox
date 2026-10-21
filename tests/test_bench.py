"""Smoke test for the bloxorz.bench package."""


def test_bench_package_imports_cleanly() -> None:
    """Verifies that bloxorz.bench and its public interface import cleanly."""
    import bloxorz.bench
    from bloxorz.bench import BenchmarkRecord, BenchmarkRunner, SearchResult, Stats

    assert bloxorz.bench is not None
    assert BenchmarkRecord is not None
    assert BenchmarkRunner is not None
    assert SearchResult is not None
    assert Stats is not None
