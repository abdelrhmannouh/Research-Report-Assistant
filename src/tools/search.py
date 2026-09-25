from typing import Any, Callable

from langchain.tools import tool
from langchain_core.tools import BaseTool

from src.models import Source


class SourceCollector:
    """Collects the web results seen during one pipeline run.

    Each unique URL gets a stable number so the LLM can cite it as [n] and
    the final report can list it under Sources.
    """

    def __init__(self) -> None:
        self._by_url: dict[str, Source] = {}

    def add(self, title: str, url: str, snippet: str = "") -> Source:
        if url not in self._by_url:
            self._by_url[url] = Source(
                id=len(self._by_url) + 1, title=title or url, url=url, snippet=snippet
            )
        return self._by_url[url]

    @property
    def sources(self) -> list[Source]:
        return list(self._by_url.values())


def format_results(results: list[dict[str, Any]], collector: SourceCollector) -> str:
    if not results:
        return "No results found."
    blocks = []
    for r in results:
        source = collector.add(r.get("title", ""), r["url"], r.get("content", ""))
        blocks.append(f"[{source.id}] {source.title}: {r.get('content', '')} ({source.url})")
    return "\n\n".join(blocks)


def make_web_search_tool(
    collector: SourceCollector, search: Callable[[str], Any]
) -> BaseTool:
    """Build a web_search tool that records every result in `collector`.

    `search` takes a query and returns a Tavily response (a dict with
    "results", or a list of results).
    """

    @tool
    def web_search(query: str) -> str:
        """
        Search the web for current information on a given topic or question.
        Use this when you need up-to-date facts, news, or information
        that may not be in your training data. Each result is numbered [n];
        cite those numbers in your notes.
        """
        try:
            response = search(query)
            results = response.get("results", []) if isinstance(response, dict) else response
            return format_results(results, collector)
        except Exception as e:
            return f"Search failed: {e}. Try a different query."

    return web_search


def make_tavily_search(api_key: str, max_results: int) -> Callable[[str], Any]:
    from langchain_tavily import TavilySearch

    tavily = TavilySearch(max_results=max_results, topic="general", tavily_api_key=api_key)
    return lambda query: tavily.invoke({"query": query})
