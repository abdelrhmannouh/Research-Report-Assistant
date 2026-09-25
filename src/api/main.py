import json
import logging
from collections.abc import Iterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config import MissingConfigError
from src.models import ReportResult
from src.pipeline.pipeline import ReportPipeline

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research Report Assistant API",
    description="Research a topic on the web and turn it into a cited report.",
    version="1.0.0",
)


class ReportRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)


def get_pipeline() -> ReportPipeline:
    try:
        return ReportPipeline()
    except MissingConfigError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reports", response_model=ReportResult)
def create_report(
    request: ReportRequest, pipeline: ReportPipeline = Depends(get_pipeline)
) -> ReportResult:
    try:
        return pipeline.run(request.topic.strip())
    except Exception as e:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=502, detail=f"Report generation failed: {e}") from e


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


@app.post("/reports/stream")
def stream_report(
    request: ReportRequest, pipeline: ReportPipeline = Depends(get_pipeline)
) -> StreamingResponse:
    """Server-sent events: `stage` per progress update, then `result` or `error`."""

    def events() -> Iterator[str]:
        try:
            for item in pipeline.run_stream(request.topic.strip()):
                kind = "result" if isinstance(item, ReportResult) else "stage"
                yield _sse(kind, item.model_dump_json())
        except Exception as e:
            logger.exception("Report generation failed")
            yield _sse("error", json.dumps({"detail": f"Report generation failed: {e}"}))

    # A sync generator is iterated in Starlette's threadpool, so the blocking
    # LLM calls don't stall the event loop.
    return StreamingResponse(events(), media_type="text/event-stream")
