import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional

import tarzi
from pydantic import BaseModel, Field
from typing_extensions import override

from ..base import BaseSearch, SearchResult, SourceItem, get_proxy_from_env

logger = logging.getLogger(__name__)

MAX_CONCURRENT_ENGINE_CALLS = 4
"""Upper bound on simultaneous native searches.

Each call drives a headless browser for tens of seconds. Running them on the
default executor would let a handful of searches occupy the thread pool that the
host application shares with all other `to_thread` work.
"""

SHUTDOWN_WAIT_SEC = 5.0
"""How long `cleanup()` waits for an in-flight search before giving up."""

_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = threading.Lock()


def _engine_executor() -> ThreadPoolExecutor:
    """Return the process-wide executor used for blocking tarzi calls."""
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(
                max_workers=MAX_CONCURRENT_ENGINE_CALLS,
                thread_name_prefix="wizsearch-tarzi",
            )
        return _executor


class TarziSearchError(Exception):
    """Custom exception for Tarzi Search errors."""


class TarziSearchConfig(BaseModel):
    search_engine: str = Field(default="brave", description="Search engine to use")
    max_results: int = Field(default=10, description="Maximum number of results to return")
    timeout: int = Field(default=15, description="Timeout in seconds")
    web_driver: str = Field(default="chromedriver", description="Web driver to use")
    headless: bool = Field(
        default=True, description="Enable headless browser mode (no visible window). Set to False for debugging."
    )
    output_format: str = Field(default="markdown", description="Output format (html|markdown|json|yaml)")
    proxy: Optional[str] = Field(
        default=None,
        description="Proxy URL (e.g., http://proxy:port). Falls back to HTTPS_PROXY/HTTP_PROXY env vars.",
    )


class TarziSearch(BaseSearch):
    def __init__(self, config: TarziSearchConfig):
        self.tarzi_config = config
        fetch_mode = "browser_headless" if config.headless else "browser_head"
        # Resolve proxy: env vars take priority, then explicit config value.
        # Note: tarzi's Rust core also reads HTTPS_PROXY/HTTP_PROXY env vars automatically
        # inside WebFetcher::from_config(). The proxy line in TOML is only needed when an
        # explicit config proxy is provided without a corresponding env var.
        proxy = get_proxy_from_env(config.proxy)
        proxy_line = f'proxy = "{proxy}"' if proxy else ""
        _config_str = f"""
[fetcher]
timeout = {config.timeout}
format = "{config.output_format}"
web_driver = "{config.web_driver}"
mode = "{fetch_mode}"
{proxy_line}
[search]
engine = "{config.search_engine}"
limit = {config.max_results}
"""
        self._config = tarzi.Config.from_str(_config_str)
        self._engine = tarzi.SearchEngine.from_config(self._config)
        # tarzi's search takes `&mut self`, so overlapping calls on one engine
        # are rejected with "Already borrowed".
        self._engine_lock = threading.Lock()

    @override
    async def search(self, query: str) -> SearchResult:
        """Perform an search query."""
        try:
            # Run the blocking search off the event loop thread. tarzi releases
            # the GIL during the request, so the caller's loop stays responsive.
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(_engine_executor(), self._search_blocking, query)
            return self._convert_to_search_result(results, query)
        except Exception as e:
            logger.error(f"Tarzi search failed for query '{query}': {e}")
            raise TarziSearchError(f"Search failed: {e}")

    def _search_blocking(self, query: str) -> List[Any]:
        """Call the native engine, one request at a time per instance."""
        with self._engine_lock:
            return self._engine.search(query, self.tarzi_config.max_results)

    def _convert_to_search_result(self, results: tarzi.SearchResult, query: str) -> SearchResult:
        """Convert tarzi SearchResult to our SearchResult format."""
        try:
            sources = []

            # Convert each result to SourceItem
            for i, result in enumerate(results):
                # Convert rank to a score between 0 and 1
                # Higher rank (lower number) should have higher score
                # Use a simple inverse ranking: score = 1 / (rank + 1)
                # This ensures score is between 0 and 1, with rank 0 getting score 1.0
                score = 1.0 / (result.rank + 1) if result.rank is not None else 1.0 / (i + 1)

                source_item = SourceItem(
                    url=result.url,
                    title=result.title,
                    content=result.snippet,  # Use snippet as content
                    score=score,
                    raw_content=None,
                )
                sources.append(source_item)

            # Create SearchResult
            search_result = SearchResult(
                query=query,
                answer=None,  # Tarzi doesn't provide AI-generated answers
                images=[],  # Tarzi doesn't provide images
                sources=sources,
                response_time=None,  # Tarzi doesn't provide response time
                raw_response=results,  # Store original results
                follow_up_questions=None,  # Tarzi doesn't provide follow-up questions
            )

            return search_result

        except Exception as e:
            logger.error(f"Failed to convert tarzi results: {e}")
            raise TarziSearchError(f"Result conversion failed: {e}")

    def cleanup(self):
        """Clean up resources and shutdown the search engine."""
        engine = getattr(self, "_engine", None)
        if not engine:
            return

        lock = getattr(self, "_engine_lock", None)
        if lock is not None and not lock.acquire(timeout=SHUTDOWN_WAIT_SEC):
            logger.warning("Skipping tarzi engine shutdown: a search is still in flight")
            return
        try:
            engine.shutdown()
        except Exception as e:
            logger.warning(f"Error during engine cleanup: {e}")
        finally:
            if lock is not None:
                lock.release()

    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        self.cleanup()
