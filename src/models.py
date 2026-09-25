import re
from typing import Literal

from pydantic import BaseModel, Field

Stage = Literal["research", "analyze", "write"]


class Source(BaseModel):
    id: int
    title: str
    url: str
    snippet: str = ""


class StageEvent(BaseModel):
    stage: Stage
    status: Literal["started", "completed"]
    elapsed: float | None = None
    detail: str = ""


class ReportResult(BaseModel):
    topic: str
    report: str
    sources: list[Source] = Field(default_factory=list)
    timings: dict[str, float] = Field(default_factory=dict)

    @property
    def filename(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", self.topic.lower()).strip("_")[:60]
        return f"{slug or 'research'}_report.md"

    def to_markdown(self) -> str:
        """The report plus a numbered Sources section, ready to save or render."""
        if not self.sources:
            return self.report
        lines = [f"{s.id}. [{s.title}]({s.url})" for s in self.sources]
        return f"{self.report.rstrip()}\n\n## Sources\n\n" + "\n".join(lines) + "\n"
