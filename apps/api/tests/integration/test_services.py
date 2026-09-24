import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from tests.support.constants import (
    NON_EXISTENT_UUID,
    SERVICE_CARDIOLOGY,
    SERVICE_DERMATOLOGY,
    SERVICE_FOLLOW_UP,
    SERVICE_GENERAL,
)
from tests.support.problem import assert_problem

pytestmark = pytest.mark.integration


def test_list_active_services(client: TestClient) -> None:
    response = client.get("/v1/services")

    assert response.status_code == 200
    ids = {service["id"] for service in response.json()}
    assert ids == {
        str(SERVICE_CARDIOLOGY),
        str(SERVICE_DERMATOLOGY),
        str(SERVICE_GENERAL),
        str(SERVICE_FOLLOW_UP),
    }


def test_inactive_service_is_not_listed(
    client: TestClient,
    db_connection: Connection,
) -> None:
    db_connection.execute(
        "UPDATE services SET is_active = FALSE WHERE id = %s",
        (SERVICE_CARDIOLOGY,),
    )

    response = client.get("/v1/services")

    assert response.status_code == 200
    ids = {service["id"] for service in response.json()}
    assert str(SERVICE_CARDIOLOGY) not in ids


def test_get_existing_service(client: TestClient) -> None:
    response = client.get(f"/v1/services/{SERVICE_CARDIOLOGY}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(SERVICE_CARDIOLOGY)
    assert body["code"] == "cardiology_initial_consultation"
    assert body["currency"] == "BRL"
    assert body["duration_minutes"] == 45


def test_get_nonexistent_service_returns_404(client: TestClient) -> None:
    response = client.get(f"/v1/services/{NON_EXISTENT_UUID}")

    assert_problem(response, 404, detail="Service not found.")


def test_get_inactive_service_returns_404(
    client: TestClient,
    db_connection: Connection,
) -> None:
    db_connection.execute(
        "UPDATE services SET is_active = FALSE WHERE id = %s",
        (SERVICE_CARDIOLOGY,),
    )

    response = client.get(f"/v1/services/{SERVICE_CARDIOLOGY}")

    assert response.status_code == 404


def test_list_payment_methods_for_service(client: TestClient) -> None:
    response = client.get(
        f"/v1/services/{SERVICE_CARDIOLOGY}/payment-methods"
    )

    assert response.status_code == 200
    methods_by_code = {
        method["code"]: method
        for method in response.json()
    }
    assert set(methods_by_code) == {"pix", "credit_card", "debit_card"}
    assert methods_by_code["credit_card"]["max_installments"] == 6


def test_list_payment_methods_for_nonexistent_service_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/services/{NON_EXISTENT_UUID}/payment-methods"
    )

    assert_problem(response, 404, detail="Service not found.")
