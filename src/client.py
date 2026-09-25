import json
from collections.abc import Iterator

import httpx

from src.models import ReportResult, StageEvent


class ReportError(RuntimeError):
    """A report could not be generated; the message is safe to show users."""


class ReportClient:
    """Generates reports through the API when `api_url` is set, else in-process."""

    def __init__(self, api_url: str = "") -> None:
        self.api_url = api_url.rstrip("/")

    @property
    def mode(self) -> str:
        return f"API ({self.api_url})" if self.api_url else "In-process"

    def stream(self, topic: str) -> Iterator[StageEvent | ReportResult]:
        if self.api_url:
            yield from self._stream_http(topic)
        else:
            yield from self._stream_local(topic)

    def _stream_local(self, topic: str) -> Iterator[StageEvent | ReportResult]:
        # Imported lazily so API mode doesn't need the LLM stack configured.
        from src.config import MissingConfigError
        from src.pipeline.pipeline import ReportPipeline

        try:
            yield from ReportPipeline().run_stream(topic)
        except MissingConfigError as e:
            raise ReportError(str(e)) from e
        except Exception as e:
            raise ReportError(f"Report generation failed: {e}") from e

    def _stream_http(self, topic: str) -> Iterator[StageEvent | ReportResult]:
        try:
            with httpx.stream(
                "POST", f"{self.api_url}/reports/stream",
                json={"topic": topic}, timeout=httpx.Timeout(10.0, read=300.0),
            ) as response:
                if response.status_code != 200:
                    response.read()
                    raise ReportError(_error_detail(response))
                for event, data in _parse_sse(response.iter_lines()):
                    payload = json.loads(data)
                    if event == "stage":
                        yield StageEvent.model_validate(payload)
                    elif event == "result":
                        yield ReportResult.model_validate(payload)
                    elif event == "error":
                        raise ReportError(payload.get("detail", "Unknown error"))
        except httpx.HTTPError as e:
            raise ReportError(f"Could not reach the API at {self.api_url}: {e}") from e


def _error_detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    if isinstance(detail, list):  # FastAPI validation errors
        detail = "; ".join(d.get("msg", "") for d in detail)
    return detail or f"API returned HTTP {response.status_code}"


def _parse_sse(lines: Iterator[str]) -> Iterator[tuple[str, str]]:
    event, data = "message", []
    for line in lines:
        if not line:
            if data:
                yield event, "\n".join(data)
            event, data = "message", []
        elif line.startswith("event:"):
            event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data.append(line[len("data:"):].strip())
    if data:
        yield event, "\n".join(data)
