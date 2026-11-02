"""Route tests for /v1/prompts.

Bedrock and DynamoDB are replaced with in-memory fakes — no real AWS calls are
made, no AWS credentials are required to run this file.
"""

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.config import settings
from app.main import app
from app.models.schemas import PromptRecord
from app.repositories.trace_repository import TracePersistenceError
from app.services.bedrock import BedrockResult

SUPPORTED_MODEL_ID = settings.SUPPORTED_MODEL_IDS[0]


class FakeBedrockService:
    def invoke(self, prompt: str, model_id: str) -> BedrockResult:
        return BedrockResult(completion="Hello there!", inference_latency_ms=12.5)


class FakeTraceRepository:
    def __init__(self, fail_on_put: bool = False) -> None:
        self.records: dict[str, PromptRecord] = {}
        self.fail_on_put = fail_on_put

    def put_record(self, record: PromptRecord) -> None:
        if self.fail_on_put:
            raise TracePersistenceError("ProvisionedThroughputExceededException")
        self.records[record.request_id] = record

    def get_record(self, request_id: str) -> PromptRecord | None:
        return self.records.get(request_id)


@pytest.fixture
def repo(monkeypatch) -> FakeTraceRepository:
    fake = FakeTraceRepository()
    monkeypatch.setattr(routes, "_bedrock_service", FakeBedrockService())
    monkeypatch.setattr(routes, "_trace_repository", fake)
    return fake


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _post(client: TestClient):
    return client.post("/v1/prompts", json={"prompt": "Say hello.", "model_id": SUPPORTED_MODEL_ID})


def test_post_persists_record_before_responding(client, repo):
    resp = _post(client)

    assert resp.status_code == 200
    body = resp.json()
    record = repo.records[body["request_id"]]
    assert resp.headers["X-Request-ID"] == body["request_id"]
    assert record.prompt == "Say hello."
    assert record.completion == body["completion"] == "Hello there!"
    assert record.total_request_latency_ms == body["total_request_latency_ms"]
    assert record.timestamp.isoformat() == body["timestamp"].replace("Z", "+00:00")


def test_post_returns_500_without_completion_when_persistence_fails(client, repo):
    repo.fail_on_put = True

    resp = _post(client)

    assert resp.status_code == 500
    request_id = resp.headers["X-Request-ID"]
    assert resp.json() == {"error": "trace_persistence_failed", "request_id": request_id}
    assert "completion" not in resp.text
    assert "Hello there!" not in resp.text


def test_get_returns_record(client, repo):
    request_id = _post(client).json()["request_id"]

    resp = client.get(f"/v1/prompts/{request_id}")

    assert resp.status_code == 200
    assert PromptRecord.model_validate(resp.json()) == repo.records[request_id]


def test_get_returns_404_when_missing(client, repo):
    resp = client.get("/v1/prompts/01JBXYZ0000000000000000000")

    assert resp.status_code == 404
    assert resp.json() == {"error": "trace_not_found", "request_id": "01JBXYZ0000000000000000000"}
