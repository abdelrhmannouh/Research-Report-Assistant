import pytest
from langchain_core.language_models import FakeListChatModel

from src.config import Settings
from src.pipeline.pipeline import ReportPipeline


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None, groq_api_key="test", tavily_api_key="test", retry_backoff_seconds=0
    )


def fake_researcher(topic, collector):
    collector.add("Source A", "https://a.example", "alpha")
    collector.add("Source B", "https://b.example", "beta")
    return f"notes on {topic} [1][2]"


@pytest.fixture
def make_pipeline(settings):
    def make(researcher=fake_researcher, **kwargs):
        llm = FakeListChatModel(responses=["- point [1]", "Report body [1]."])
        return ReportPipeline(llm=llm, researcher=researcher, settings=settings, **kwargs)

    return make
