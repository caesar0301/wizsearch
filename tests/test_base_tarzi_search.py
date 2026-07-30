"""
Unit tests for the tarzi-backed engine wrapper.

These use a fake engine object, so they need neither tarzi nor a WebDriver. They
pin the two properties the wrapper is responsible for: the caller's event loop
stays responsive while a blocking search runs, and overlapping searches on one
engine instance are serialized (tarzi's search takes `&mut self` and rejects
concurrent access with "Already borrowed").
"""

import asyncio
import threading
import time

import pytest

from wizsearch.engines.base_tarzi_search import (
    TarziSearch,
    TarziSearchConfig,
    TarziSearchError,
)

CALL_DURATION_SEC = 0.4
TICK_INTERVAL_SEC = 0.02


class FakeResult:
    def __init__(self, rank: int):
        self.url = f"https://example.com/{rank}"
        self.title = f"Result {rank}"
        self.snippet = "snippet"
        self.rank = rank


class FakeEngine:
    """Stand-in for `tarzi.SearchEngine` that sleeps and detects overlap."""

    def __init__(self, duration=CALL_DURATION_SEC, fail=False):
        self.duration = duration
        self.fail = fail
        self.calls = []
        self.max_concurrency = 0
        self._active = 0
        self._guard = threading.Lock()

    def search(self, query, max_results):
        with self._guard:
            self._active += 1
            self.max_concurrency = max(self.max_concurrency, self._active)
        try:
            time.sleep(self.duration)
            if self.fail:
                raise RuntimeError("engine exploded")
            self.calls.append((query, max_results))
            return [FakeResult(i) for i in range(min(max_results, 2))]
        finally:
            with self._guard:
                self._active -= 1

    def shutdown(self):
        pass


def _make_search(engine=None, **config_kwargs):
    """Build a TarziSearch with its native engine replaced by a fake."""
    search = TarziSearch.__new__(TarziSearch)
    search.tarzi_config = TarziSearchConfig(**config_kwargs)
    search._engine = engine or FakeEngine()
    search._engine_lock = threading.Lock()
    return search


@pytest.mark.asyncio
async def test_search_keeps_event_loop_responsive():
    """The loop keeps ticking while the blocking call is in flight."""
    search = _make_search()
    ticks = 0

    async def tick():
        nonlocal ticks
        while True:
            await asyncio.sleep(TICK_INTERVAL_SEC)
            ticks += 1

    ticker = asyncio.create_task(tick())
    result = await search.search("vision language models")
    ticker.cancel()

    assert len(result.sources) == 2
    assert ticks >= 5, f"event loop starved during search ({ticks} ticks)"


@pytest.mark.asyncio
async def test_concurrent_searches_are_serialized():
    """One instance never runs two native calls at once."""
    engine = FakeEngine(duration=0.2)
    search = _make_search(engine=engine)

    results = await asyncio.gather(*(search.search(f"query {i}") for i in range(4)))

    assert len(results) == 4
    assert engine.max_concurrency == 1, "overlapping calls would hit 'Already borrowed'"
    assert len(engine.calls) == 4


@pytest.mark.asyncio
async def test_search_wraps_engine_failure():
    """Native failures surface as TarziSearchError."""
    search = _make_search(engine=FakeEngine(duration=0.0, fail=True))

    with pytest.raises(TarziSearchError):
        await search.search("boom")


@pytest.mark.asyncio
async def test_cleanup_skips_shutdown_while_search_runs(monkeypatch):
    """A busy engine is not shut down underneath an in-flight search."""
    monkeypatch.setattr("wizsearch.engines.base_tarzi_search.SHUTDOWN_WAIT_SEC", 0.05)
    shutdown_calls = []

    engine = FakeEngine(duration=0.3)
    engine.shutdown = lambda: shutdown_calls.append(True)
    search = _make_search(engine=engine)

    task = asyncio.create_task(search.search("busy"))
    await asyncio.sleep(0.1)
    search.cleanup()
    await task

    assert shutdown_calls == []

    search.cleanup()
    assert shutdown_calls == [True]
