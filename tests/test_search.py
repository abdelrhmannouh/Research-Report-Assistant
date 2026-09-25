from src.tools.search import SourceCollector, make_web_search_tool


def test_collector_dedupes_and_numbers_sources():
    c = SourceCollector()
    assert c.add("A", "https://a").id == 1
    assert c.add("B", "https://b").id == 2
    assert c.add("A again", "https://a").id == 1
    assert [s.url for s in c.sources] == ["https://a", "https://b"]


def test_tool_formats_results_and_records_sources():
    c = SourceCollector()
    response = {"results": [
        {"title": "T1", "url": "https://one", "content": "first"},
        {"title": "T2", "url": "https://two", "content": "second"},
    ]}
    tool = make_web_search_tool(c, lambda q: response)
    out = tool.invoke({"query": "x"})
    assert "[1] T1: first (https://one)" in out
    assert "[2] T2: second (https://two)" in out
    assert len(c.sources) == 2


def test_tool_handles_empty_and_failing_search():
    c = SourceCollector()
    assert make_web_search_tool(c, lambda q: {"results": []}).invoke({"query": "x"}) == "No results found."

    def boom(q):
        raise RuntimeError("down")

    assert "Search failed: down" in make_web_search_tool(c, boom).invoke({"query": "x"})
