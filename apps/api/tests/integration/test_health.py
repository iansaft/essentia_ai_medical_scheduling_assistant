import pytest
from fastapi.testclient import TestClient

from essentia_api.api.routes import health as health_module

pytestmark = pytest.mark.integration


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_n8n_health_returns_ok_when_n8n_is_ready(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health_module,
        "probe_n8n_readiness",
        lambda _base_url: True,
    )

    response = client.get("/health/n8n")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_n8n_health_returns_unavailable_when_n8n_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health_module,
        "probe_n8n_readiness",
        lambda _base_url: False,
    )

    response = client.get("/health/n8n")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "error"}


def test_n8n_health_probe_uses_configured_base_url(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake_probe(base_url: str) -> bool:
        seen.append(base_url)
        return True

    monkeypatch.setattr(
        health_module,
        "probe_n8n_readiness",
        fake_probe,
    )

    response = client.get("/health/n8n")

    assert response.status_code == 200
    assert seen == [client.app.state.settings.n8n_base_url]


def test_allowed_origin_receives_cors_headers(client: TestClient) -> None:
    response = client.get(
        "/v1/patients",
        headers={
            "Origin": "http://localhost:5173",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )


def test_n8n_health_receives_cors_headers_for_web_origin(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health_module,
        "probe_n8n_readiness",
        lambda _base_url: True,
    )

    response = client.get(
        "/health/n8n",
        headers={
            "Origin": "http://localhost:8080",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:8080"
    )


def test_disallowed_origin_does_not_receive_cors_headers(
    client: TestClient,
) -> None:
    response = client.get(
        "/v1/patients",
        headers={
            "Origin": "http://evil.example.com",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_for_patients(client: TestClient) -> None:
    response = client.options(
        "/v1/patients",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:8080"
    )
