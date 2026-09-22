import pytest
from fastapi.testclient import TestClient

from tests.support.constants import NON_EXISTENT_UUID, PATIENT_MARIA


pytestmark = pytest.mark.integration


def test_get_existing_patient(client: TestClient) -> None:
    response = client.get(f"/v1/patients/{PATIENT_MARIA}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(PATIENT_MARIA)
    assert body["full_name"] == "Maria Silva"
    assert body["is_active"] is True


def test_get_nonexistent_patient_returns_404(client: TestClient) -> None:
    response = client.get(f"/v1/patients/{NON_EXISTENT_UUID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found."


def test_get_patient_with_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/v1/patients/not-a-uuid")

    assert response.status_code == 422
