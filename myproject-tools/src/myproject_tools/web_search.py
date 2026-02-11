import asyncio

from ddgs import DDGS
from pydantic import BaseModel

from myproject_tools.web_fetch import fetch_page


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    full_content: str | None = None
    # For news results
    date: str | None = None
    source: str | None = None


async def search_web(query: str, max_results: int = 5, fetch_full: bool = False) -> list[SearchResult]:
    results = []
    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(
                query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results,
            )

            for r in search_results:
                # Instantiate the class directly
                item = SearchResult(
                    title=r.get("title", ""), url=r.get("href", ""), snippet=r.get("body", "")
                )

                if fetch_full:
                    full_data = await fetch_page(item.url)
                    item.full_content = full_data.content

                results.append(item)

        return results
    except Exception as e:
        print(f"DDGS Search Error: {e}")
        return []


async def search_news(query: str, max_results: int = 5, fetch_full: bool = False) -> list[SearchResult]:
    results = []
    try:
        with DDGS() as ddgs:
            # await the async call
            news_results = ddgs.news(query, max_results=max_results)

            for r in news_results:
                item = SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),  # News results use 'url' instead of 'href'
                    snippet=r.get("body", ""),
                    date=r.get("date"),
                    source=r.get("source"),
                )

                if fetch_full:
                    full_data = await fetch_page(item.url)
                    item.full_content = full_data.content

                results.append(item)
        return results
    except Exception as e:
        print(f"DDGS News Error: {e}")
        return []


async def main():
    # Example: Deep Web Search
    print("--- Web Search with Content ---")
    web_results = await search_web(query="Small Language Model deployment", max_results=1, fetch_full=True)
    for res in web_results:
        print(f"Title: {res.title}")
        if res.full_content:
            print(f"Full Content: {res.full_content[:500]}...\n")

    # Example: Deep News Search (Requested)
    print("--- News Search with Content ---")
    news_results = await search_news(query="Australian news", max_results=1, fetch_full=True)
    for res in news_results:
        print(f"Source: {res.source} | Date: {res.date}")
        print(f"Title: {res.title}")
        print(f"Snippet: {res.snippet}")
        if res.full_content:
            print(f"Full Content: {res.full_content[:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
