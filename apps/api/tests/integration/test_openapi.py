import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

EXPECTED_OPERATIONS = {
    "/health": {"get"},
    "/health/n8n": {"get"},
    "/v1/patients": {"get", "post"},
    "/v1/patients/{patient_id}": {"get"},
    "/v1/patients/{patient_id}/appointments": {"get"},
    "/v1/services": {"get"},
    "/v1/services/{service_id}": {"get"},
    "/v1/services/{service_id}/payment-methods": {"get"},
    "/v1/availability": {"get"},
    "/v1/appointments/{appointment_id}": {"get"},
    "/v1/appointments": {"post"},
    "/v1/appointments/{appointment_id}/cancel": {"post"},
}


def test_openapi_contains_all_public_api_operations(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]

    for path, methods in EXPECTED_OPERATIONS.items():
        assert path in paths
        assert methods.issubset(paths[path])


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/v1/appointments", "post"),
        ("/v1/appointments/{appointment_id}/cancel", "post"),
    ],
)
def test_mutating_appointment_operations_document_required_idempotency_header(
    client: TestClient,
    path: str,
    method: str,
) -> None:
    schema = client.get("/openapi.json").json()
    parameters = schema["paths"][path][method]["parameters"]
    idempotency_parameter = next(
        parameter
        for parameter in parameters
        if parameter["name"] == "Idempotency-Key"
    )

    assert idempotency_parameter["in"] == "header"
    assert idempotency_parameter["required"] is True


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/v1/patients/{patient_id}", "get"),
        ("/v1/patients/{patient_id}/appointments", "get"),
        ("/v1/appointments", "post"),
        ("/v1/appointments/{appointment_id}", "get"),
        ("/v1/appointments/{appointment_id}/cancel", "post"),
    ],
)
def test_patient_scoped_operations_document_required_identity_header(
    client: TestClient,
    path: str,
    method: str,
) -> None:
    schema = client.get("/openapi.json").json()
    parameters = schema["paths"][path][method]["parameters"]
    identity_parameter = next(
        parameter
        for parameter in parameters
        if parameter["name"] == "X-Patient-Id"
    )

    assert identity_parameter["in"] == "header"
    assert identity_parameter["required"] is True


def test_public_operations_do_not_require_identity_header(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()

    for path, method in (
        ("/v1/patients", "get"),
        ("/v1/patients", "post"),
        ("/v1/services", "get"),
        ("/v1/availability", "get"),
    ):
        parameters = schema["paths"][path][method].get("parameters", [])
        names = {parameter["name"] for parameter in parameters}
        assert "X-Patient-Id" not in names
