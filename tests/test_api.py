import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.main import app, get_pipeline
from src.client import _parse_sse


@pytest.fixture
def client(make_pipeline):
    app.dependency_overrides[get_pipeline] = lambda: make_pipeline()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_report(client):
    body = client.post("/reports", json={"topic": "batteries"}).json()
    assert body["report"] == "Report body [1]."
    assert len(body["sources"]) == 2


def test_rejects_short_topic(client):
    assert client.post("/reports", json={"topic": "  "}).status_code == 422


def test_stream_emits_stage_events_then_result(client):
    with client.stream("POST", "/reports/stream", json={"topic": "batteries"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = list(_parse_sse(r.iter_lines()))
    kinds = [e for e, _ in events]
    assert kinds == ["stage"] * 6 + ["result"]
    assert json.loads(events[-1][1])["topic"] == "batteries"


def test_stream_reports_pipeline_errors(make_pipeline):
    def broken(topic, collector):
        raise RuntimeError("tavily down")

    app.dependency_overrides[get_pipeline] = lambda: make_pipeline(researcher=broken)
    try:
        with TestClient(app).stream("POST", "/reports/stream", json={"topic": "abc"}) as r:
            events = list(_parse_sse(r.iter_lines()))
    finally:
        app.dependency_overrides.clear()
    assert events[-1][0] == "error"
    assert "tavily down" in json.loads(events[-1][1])["detail"]


def test_missing_config_returns_503():
    def missing():
        raise HTTPException(503, "GROQ_API_KEY is missing — add it to your .env file.")

    app.dependency_overrides[get_pipeline] = missing
    try:
        r = TestClient(app).post("/reports", json={"topic": "abc"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 503
    assert "GROQ_API_KEY" in r.json()["detail"]
