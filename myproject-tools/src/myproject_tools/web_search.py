import asyncio

from ddgs import DDGS

from myproject_tools.web_fetch import fetch_page


async def search_web(query: str, max_results: int = 5, fetch_full: bool = False) -> list[dict]:
    results = []
    try:
        # The library uses the same class for both, just change the 'with' to 'async with'
        with DDGS() as ddgs:
            # Notice we call .text() and it returns a list directly in newer versions
            search_results = ddgs.text(
                query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results,
            )

            for r in search_results:
                item = {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}

                if fetch_full:
                    # Await our local fetcher
                    full_data = await fetch_page(item["url"])
                    item["full_content"] = full_data.get("content")

                results.append(item)

        return results
    except Exception as e:
        print(f"DDGS Search Error: {e}")
        return []


async def search_news(query: str, max_results: int = 5) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            # Same pattern for news
            news_results = ddgs.news(query, max_results=max_results)
            for r in news_results:
                results.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "date": r.get("date"),
                        "source": r.get("source"),
                        "snippet": r.get("body"),
                    }
                )
        return results
    except Exception as e:
        print(f"DDGS News Error: {e}")
        return []


async def main():
    # Example: Just snippets
    print("--- Basic Search ---")
    basic = await search_web(query="Small Language Model", max_results=2)
    print(basic)

    # Example: Deep Search (Integration test)
    print("\n--- Deep Search (with Markdown) ---")
    deep = await search_web(query="latest arxiv papers on SLM", max_results=1, fetch_full=True)
    if deep:
        print(f"Title: {deep[0]['title']}")
        print(f"Content Preview: {deep[0].get('full_content', '')[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
