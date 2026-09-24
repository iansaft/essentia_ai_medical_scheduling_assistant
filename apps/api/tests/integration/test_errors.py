import pytest
from fastapi.testclient import TestClient

from essentia_api.api.routes import patients as patients_module
from tests.support.constants import (
    NON_EXISTENT_UUID,
    PATIENT_MARIA,
)
from tests.support.problem import assert_problem

pytestmark = pytest.mark.integration


def test_correlation_id_is_generated_when_absent(
    client: TestClient,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    correlation_id = response.headers["x-correlation-id"]
    assert correlation_id
    assert correlation_id != ""


def test_inbound_correlation_id_is_echoed(
    client: TestClient,
) -> None:
    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "trace-abc-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "trace-abc-123"


def test_correlation_id_present_on_problem_response(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/appointments/{NON_EXISTENT_UUID}",
        headers={
            "X-Patient-Id": str(PATIENT_MARIA),
            "X-Correlation-ID": "trace-on-error",
        },
    )

    assert_problem(
        response,
        404,
        detail="Appointment not found.",
    )
    assert response.headers["x-correlation-id"] == "trace-on-error"


def test_unhandled_error_returns_problem_json(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args, **_kwargs):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(
        patients_module.patient_queries,
        "list_patients",
        boom,
    )

    # Do not enter the context manager: the session-scoped app already
    # ran lifespan, and exiting a nested TestClient would close the pool.
    no_raise_client = TestClient(
        client.app,
        raise_server_exceptions=False,
    )
    response = no_raise_client.get("/v1/patients")

    body = assert_problem(
        response,
        500,
        detail="An unexpected error occurred.",
    )
    assert body["title"] == "Internal Server Error"
    assert body["type"] == "/problems/internal-error"
    assert body["instance"] == "/v1/patients"


def test_validation_error_keeps_fastapi_detail_shape(
    client: TestClient,
) -> None:
    response = client.get(
        "/v1/patients/not-a-uuid",
        headers={"X-Patient-Id": str(PATIENT_MARIA)},
    )

    assert response.status_code == 422
    content_type = response.headers.get("content-type", "")
    assert not content_type.startswith("application/problem+json")
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert body["detail"][0]["loc"] == ["path", "patient_id"]


def test_missing_identity_header_is_422_not_problem(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{PATIENT_MARIA}",
    )

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)
    assert any(
        item.get("loc") == ["header", "X-Patient-Id"]
        for item in body["detail"]
    )
