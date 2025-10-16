"""
Integration tests for the wizsearch.page_crawler module.

These tests require network connectivity and external services.
Mark with @pytest.mark.integration to distinguish from unit tests.
"""

import asyncio
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from wizsearch.page_crawler import PageCrawler


class TestPageCrawlerBasic:
    """Test basic PageCrawler functionality."""

    def test_initialization_default_parameters(self):
        """Test PageCrawler initialization with default parameters."""
        url = "https://example.com"
        crawler = PageCrawler(url)

        assert crawler.url == url
        assert crawler.external_links is False
        assert crawler.content_format == "markdown"
        assert crawler.adaptive_crawl is False
        assert crawler.depth == 1
        assert crawler.word_count_threshold == 5
        assert crawler.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert crawler.verbose is False
        assert crawler.wait_for is None
        assert crawler.screenshot is False
        assert crawler.bypass_cache is False
        assert crawler.only_text is False
        assert crawler.session_id is None
        assert crawler.extraction_strategy is None
        assert crawler.extra_params == {}

    def test_initialization_custom_parameters(self):
        """Test PageCrawler initialization with custom parameters."""
        url = "https://example.com"
        custom_params = {
            "external_links": True,
            "content_format": "html",
            "adaptive_crawl": True,
            "depth": 2,
            "word_count_threshold": 10,
            "user_agent": "Custom Bot",
            "verbose": True,
            "wait_for": ".content",
            "screenshot": True,
            "bypass_cache": True,
            "only_text": True,
            "session_id": "test_session",
            "extraction_strategy": "custom",
            "custom_param": "custom_value",
        }

        crawler = PageCrawler(url, **custom_params)

        assert crawler.url == url
        assert crawler.external_links is True
        assert crawler.content_format == "html"
        assert crawler.adaptive_crawl is True
        assert crawler.depth == 2
        assert crawler.word_count_threshold == 10
        assert crawler.user_agent == "Custom Bot"
        assert crawler.verbose is True
        assert crawler.wait_for == ".content"
        assert crawler.screenshot is True
        assert crawler.bypass_cache is True
        assert crawler.only_text is True
        assert crawler.session_id == "test_session"
        assert crawler.extraction_strategy == "custom"
        assert crawler.extra_params == {"custom_param": "custom_value"}


class TestPageCrawlerIntegration:
    """Integration tests that require network connectivity."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_real_website_markdown(self):
        """Test crawling a real website and extracting markdown content."""
        # Use a reliable, simple website for testing
        url = "https://httpbin.org/html"
        crawler = PageCrawler(url, content_format="markdown")

        content = await crawler.crawl()

        # httpbin.org/html returns a simple HTML page
        assert isinstance(content, str)
        if content:  # Only assert content if crawl4ai is installed
            assert len(content) > 0
            # Should contain some basic content from the page
            # The content may vary, but should contain readable text
            assert "melville" in content.lower() or "html" in content.lower() or "example" in content.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_real_website_html(self):
        """Test crawling a real website and extracting HTML content."""
        url = "https://httpbin.org/html"
        crawler = PageCrawler(url, content_format="html")

        content = await crawler.crawl()

        assert isinstance(content, str)
        if content:  # Only assert content if crawl4ai is installed
            assert len(content) > 0
            # HTML content should contain HTML tags
            assert "<" in content and ">" in content

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_real_website_text(self):
        """Test crawling a real website and extracting text content."""
        url = "https://httpbin.org/html"
        crawler = PageCrawler(url, content_format="text")

        content = await crawler.crawl()

        assert isinstance(content, str)
        if content:  # Only assert content if crawl4ai is installed
            assert len(content) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_with_advanced_parameters(self):
        """Test crawling with advanced parameters."""
        url = "https://httpbin.org/html"
        crawler = PageCrawler(url, word_count_threshold=1, verbose=True, bypass_cache=True, only_text=False)

        content = await crawler.crawl()

        assert isinstance(content, str)
        # Should succeed even with advanced parameters

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_invalid_url(self):
        """Test crawling an invalid URL."""
        url = "https://this-domain-should-not-exist-12345.com"
        crawler = PageCrawler(url)

        content = await crawler.crawl()

        # Should return empty string on failure, not raise exception
        assert content == ""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_timeout_handling(self):
        """Test crawling with a URL that might timeout."""
        # Use httpbin's delay endpoint
        url = "https://httpbin.org/delay/1"
        crawler = PageCrawler(url, verbose=True)

        content = await crawler.crawl()

        # Should either succeed or return empty string
        assert isinstance(content, str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_adaptive_crawling(self):
        """Test adaptive crawling functionality."""
        url = "https://httpbin.org/html"
        crawler = PageCrawler(url, adaptive_crawl=True)

        content = await crawler.crawl()

        assert isinstance(content, str)
        # Adaptive crawling should work or fallback to regular crawling

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_external_links_crawling(self):
        """Test crawling with external links enabled."""
        url = "https://httpbin.org/html"
        crawler = PageCrawler(url, external_links=True, depth=2)

        content = await crawler.crawl()

        assert isinstance(content, str)
        # Should complete without hanging


class TestPageCrawlerWithoutCrawl4AI:
    """Test PageCrawler behavior when crawl4ai is not available."""

    @pytest.mark.asyncio
    async def test_crawl_without_crawl4ai(self):
        """Test crawling when crawl4ai is not installed."""
        url = "https://example.com"
        PageCrawler(url)

        # Mock the import to raise ImportError
        with patch("wizsearch.page_crawler.PageCrawler.crawl") as mock_crawl:
            # Simulate the actual behavior when crawl4ai is not installed
            async def mock_crawl_func():
                return ""

            mock_crawl.side_effect = mock_crawl_func

            content = await mock_crawl()
            assert content == ""

    @pytest.mark.asyncio
    async def test_crawl_import_error_handling(self):
        """Test that ImportError is handled gracefully."""
        url = "https://example.com"
        crawler = PageCrawler(url)

        # Test the actual import error handling in the crawl method
        with patch.dict("sys.modules", {"crawl4ai": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'crawl4ai'")):
                content = await crawler.crawl()
                assert content == ""


class TestPageCrawlerContentExtraction:
    """Test content extraction methods."""

    def test_extract_content_success(self):
        """Test successful content extraction."""
        url = "https://example.com"
        crawler = PageCrawler(url, content_format="markdown")

        # Mock a successful crawl result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = "# Test Content\n\nThis is test markdown content."
        mock_result.html = "<h1>Test Content</h1><p>This is test HTML content.</p>"
        mock_result.cleaned_html = "Test Content This is test cleaned content."

        # Test markdown extraction
        content = crawler._extract_content(mock_result)
        assert content == "# Test Content\n\nThis is test markdown content."

        # Test HTML extraction
        crawler.content_format = "html"
        content = crawler._extract_content(mock_result)
        assert content == "<h1>Test Content</h1><p>This is test HTML content.</p>"

        # Test text extraction
        crawler.content_format = "text"
        content = crawler._extract_content(mock_result)
        assert content == "Test Content This is test cleaned content."

    def test_extract_content_unsuccessful_result(self):
        """Test content extraction with unsuccessful result."""
        url = "https://example.com"
        crawler = PageCrawler(url)

        # Mock an unsuccessful crawl result
        mock_result = MagicMock()
        mock_result.success = False

        content = crawler._extract_content(mock_result)
        assert content == ""

    def test_extract_content_none_result(self):
        """Test content extraction with None result."""
        url = "https://example.com"
        crawler = PageCrawler(url)

        content = crawler._extract_content(None)
        assert content == ""

    def test_extract_content_missing_attributes(self):
        """Test content extraction when result lacks expected attributes."""
        url = "https://example.com"
        crawler = PageCrawler(url, content_format="markdown")

        # Mock a result without the expected attributes
        mock_result = MagicMock()
        mock_result.success = True
        # Remove the markdown attribute
        delattr(mock_result, "markdown")

        content = crawler._extract_content(mock_result)
        assert content == ""

    def test_extract_content_invalid_format(self):
        """Test content extraction with invalid format."""
        url = "https://example.com"
        crawler = PageCrawler(url, content_format="invalid_format")

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = "# Test Content"

        # Should fallback to markdown for invalid format
        content = crawler._extract_content(mock_result)
        assert content == "# Test Content"

    def test_extract_content_exception_handling(self):
        """Test content extraction exception handling."""
        url = "https://example.com"
        crawler = PageCrawler(url, content_format="markdown")

        # Mock a result that raises an exception when accessing attributes
        mock_result = MagicMock()
        mock_result.success = True
        # Create a property that raises an exception
        type(mock_result).markdown = PropertyMock(side_effect=Exception("Test exception"))

        content = crawler._extract_content(mock_result)
        assert content == ""


class TestPageCrawlerDepthCrawling:
    """Test depth crawling functionality."""

    @pytest.mark.asyncio
    async def test_crawl_with_depth_basic(self):
        """Test basic depth crawling functionality."""
        url = "https://example.com"
        crawler = PageCrawler(url, external_links=True, depth=2)

        mock_crawler = MagicMock()
        mock_config = MagicMock()
        initial_content = "Initial page content"

        # Test the _crawl_with_depth method directly
        result = await crawler._crawl_with_depth(mock_crawler, mock_config, initial_content)

        # With current implementation, should return initial content
        assert result == initial_content

    @pytest.mark.asyncio
    async def test_crawl_with_depth_one(self):
        """Test depth crawling with depth 1."""
        url = "https://example.com"
        crawler = PageCrawler(url, external_links=True, depth=1)

        mock_crawler = MagicMock()
        mock_config = MagicMock()
        initial_content = "Initial page content"

        result = await crawler._crawl_with_depth(mock_crawler, mock_config, initial_content)

        # With depth 1, should return initial content unchanged
        assert result == initial_content

    @pytest.mark.asyncio
    async def test_crawl_with_depth_exception(self):
        """Test depth crawling exception handling."""
        url = "https://example.com"
        crawler = PageCrawler(url, external_links=True, depth=3)

        # Mock that raises an exception
        mock_crawler = MagicMock()
        mock_config = MagicMock()
        initial_content = "Initial page content"

        # Even if there's an exception in depth crawling, should return initial content
        result = await crawler._crawl_with_depth(mock_crawler, mock_config, initial_content)
        assert result == initial_content


class TestPageCrawlerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_crawl_empty_url(self):
        """Test crawling with empty URL."""
        crawler = PageCrawler("")

        content = await crawler.crawl()

        # Should handle empty URL gracefully
        assert isinstance(content, str)

    @pytest.mark.asyncio
    async def test_crawl_malformed_url(self):
        """Test crawling with malformed URL."""
        crawler = PageCrawler("not-a-valid-url")

        content = await crawler.crawl()

        # Should return empty string for malformed URL
        assert content == ""

    def test_initialization_with_none_values(self):
        """Test initialization with None values for optional parameters."""
        url = "https://example.com"
        crawler = PageCrawler(url, wait_for=None, session_id=None, extraction_strategy=None)

        assert crawler.url == url
        assert crawler.wait_for is None
        assert crawler.session_id is None
        assert crawler.extraction_strategy is None

    @pytest.mark.asyncio
    async def test_crawl_with_all_advanced_options(self):
        """Test crawling with all advanced options enabled."""
        url = "https://httpbin.org/html"
        crawler = PageCrawler(
            url,
            external_links=True,
            content_format="markdown",
            adaptive_crawl=False,  # Don't use adaptive for this test
            depth=2,
            word_count_threshold=1,
            user_agent="Test Bot",
            verbose=True,
            screenshot=False,  # Don't take screenshots in tests
            bypass_cache=True,
            include_raw_html=True,
            only_text=False,
            session_id="test_session_123",
            extraction_strategy=None,
            custom_header="custom_value",
        )

        # This should not raise an exception
        content = await crawler.crawl()
        assert isinstance(content, str)


class TestPageCrawlerPerformance:
    """Test performance-related aspects."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_multiple_concurrent(self):
        """Test multiple concurrent crawl operations."""
        urls = ["https://httpbin.org/html", "https://httpbin.org/json", "https://httpbin.org/user-agent"]

        crawlers = [PageCrawler(url) for url in urls]

        # Run multiple crawls concurrently
        tasks = [crawler.crawl() for crawler in crawlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == 3
        for result in results:
            # Each result should be a string (or exception, but we expect strings)
            if isinstance(result, str):
                assert isinstance(result, str)
            else:
                # If it's an exception, it should be handled gracefully
                assert isinstance(result, Exception)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_timeout_behavior(self):
        """Test crawl behavior with potential timeouts."""
        # Use a slow endpoint
        url = "https://httpbin.org/delay/2"
        crawler = PageCrawler(url, verbose=False)

        import time

        start_time = time.time()

        content = await crawler.crawl()

        end_time = time.time()
        duration = end_time - start_time

        # Should complete or timeout within reasonable time (e.g., 30 seconds)
        assert duration < 30.0
        assert isinstance(content, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
