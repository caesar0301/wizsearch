#!/usr/bin/env python3
"""
Brave Search Demo
"""

import asyncio

from wizsearch import BraveSearch, BraveSearchConfig


async def demo_basic_search():
    """Demonstrate basic Brave search functionality."""
    print("=== Basic Brave Search Demo ===")

    try:
        # Initialize with custom configuration for better timeout
        search = BraveSearch(config=BraveSearchConfig())

        # Perform a basic search
        query = "甲骨文 星际之门"
        result = await search.search(query)

        print(f"Number of sources: {len(result.sources)}")

        if result.answer:
            print(f"\nDirect answer: {result.answer}")

        print("\nTop 5 results:")
        for i, source in enumerate(result.sources[:5], 1):
            print(f"\n{i}. {source.title}")
            print(f"   URL: {source.url}")
            if source.content:
                content = source.content[:200] + "..." if len(source.content) > 200 else source.content
                print(f"   Content: {content}")

    except Exception as e:
        print(f"Brave search error: {e}")


async def demo_async_search():
    """Demonstrate async Brave search functionality."""
    print("\n=== Async Search Demo ===")

    try:
        search = BraveSearch(config=BraveSearchConfig())

        # Perform multiple async searches
        queries = ["climate change solutions", "renewable energy technologies"]

        print(f"\nPerforming {len(queries)} async searches...")

        # Run searches concurrently
        tasks = [search.search(query) for query in queries]
        results = await asyncio.gather(*tasks)

        for _, result in zip(queries, results):
            print(f"Sources found: {len(result.sources)}")
            if result.sources:
                print(f"Top result: {result.sources[0].title}")

    except BraveSearchError as e:
        print(f"Brave search error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def main():
    """Run all demos."""
    print("Brave Search Demo")
    print("==================")

    # Run async demos
    await demo_basic_search()
    await demo_async_search()

    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
