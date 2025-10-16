#!/usr/bin/env python3
"""
WeChat Search Demo
"""

import asyncio

from wizsearch import WeChatSearch, WeChatSearchConfig


async def demo_basic_search():
    """Demonstrate basic WeChat search functionality."""
    print("=== Basic WeChat Search Demo ===")

    try:
        # Initialize with custom configuration for better timeout
        search = WeChatSearch(config=WeChatSearchConfig())

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
        print(f"WeChat search error: {e}")


async def main():
    """Run all demos."""
    print("WeChat Search Demo")
    print("==================")

    # Run async demos
    await demo_basic_search()

    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
