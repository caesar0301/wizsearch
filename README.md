# WizSearch

[![CI](https://github.com/caesar0301/wizsearch/actions/workflows/ci.yml/badge.svg)](https://github.com/caesar0301/wizsearch/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/wizsearch.svg)](https://pypi.org/project/wizsearch/)

A unified Python library for searching across multiple search engines with a consistent interface.

## Features

- **Multiple Search Engines**: Baidu, Bing, Brave, DuckDuckGo, Google, Google AI, SearxNG, Tavily, WeChat
- **Unified Interface**: Single API for all search engines
- **Page Crawling**: Built-in web page content extraction

## Installation

```bash
pip install wizsearch
```

## Quick Start

```python
from wizsearch import WizSearch

# Initialize with your preferred engine
searcher = WizSearch(engine="google")
results = searcher.search("your query")
```

Check the `examples/` directory for engine-specific usage.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test
```

## Status

🚧 Alpha - API may change

## License

MIT License - see [LICENSE](LICENSE) file for details.
