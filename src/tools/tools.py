from langchain.tools import tool
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

tavily_search = TavilySearch(
    max_results=3,
    topic="general",
)

@tool
def web_search(query: str) -> str:
    """
    Search the web for current information on a given topic or question.
    Use this when you need up-to-date facts, news, or information
    that may not be in your training data.
    """
    try:
        response = tavily_search.invoke({"query": query})
        results = response.get("results", []) if isinstance(response, dict) else response
        if not results:
            return "No results found."
        return "\n\n".join(
            f"{r['title']}: {r['content']} ({r['url']})" for r in results
        )
    except Exception as e:
        return f"Search failed: {e}. Try a different query."

