import pytest

from src.config import MissingConfigError, Settings
from src.models import ReportResult, StageEvent
from src.pipeline.pipeline import ReportPipeline
from tests.conftest import fake_researcher


def test_stream_emits_stages_in_order_then_result(make_pipeline):
    items = list(make_pipeline().run_stream("batteries"))
    stages = [(i.stage, i.status) for i in items if isinstance(i, StageEvent)]
    assert stages == [
        ("research", "started"), ("research", "completed"),
        ("analyze", "started"), ("analyze", "completed"),
        ("write", "started"), ("write", "completed"),
    ]
    assert items[1].detail == "2 sources"
    result = items[-1]
    assert isinstance(result, ReportResult)
    assert result.report == "Report body [1]."
    assert [s.id for s in result.sources] == [1, 2]
    assert set(result.timings) == {"research", "analyze", "write"}


def test_markdown_includes_sources_and_safe_filename(make_pipeline):
    result = make_pipeline().run("AI / energy: 2025?")
    md = result.to_markdown()
    assert md.startswith("Report body [1].")
    assert "## Sources\n\n1. [Source A](https://a.example)\n2. [Source B](https://b.example)" in md
    assert result.filename == "ai_energy_2025_report.md"


class Flaky(Exception):
    pass


def test_research_retries_then_succeeds(make_pipeline):
    calls = []

    def flaky(topic, collector):
        calls.append(1)
        if len(calls) < 3:
            collector.add("stale", "https://stale")
            raise Flaky()
        return fake_researcher(topic, collector)

    result = make_pipeline(researcher=flaky, retry_on=(Flaky,)).run("x y z")
    assert len(calls) == 3
    # Sources from failed attempts are discarded.
    assert [s.url for s in result.sources] == ["https://a.example", "https://b.example"]


def test_research_gives_up_after_max_attempts(make_pipeline):
    def always(topic, collector):
        raise Flaky()

    with pytest.raises(Flaky):
        make_pipeline(researcher=always, retry_on=(Flaky,)).run("x y z")


def test_missing_keys_raise_clear_error():
    with pytest.raises(MissingConfigError, match="GROQ_API_KEY, TAVILY_API_KEY are missing"):
        ReportPipeline(settings=Settings(_env_file=None, groq_api_key="", tavily_api_key=""))
