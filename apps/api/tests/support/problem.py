from __future__ import annotations

from httpx import Response


def assert_problem(
    response: Response,
    status: int,
    *,
    detail: str | None = None,
    title: str | None = None,
    problem_type: str | None = None,
) -> dict:
    """
    Assert an RFC 7807 application/problem+json error response.
    """
    assert response.status_code == status
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("application/problem+json")

    body = response.json()
    assert body["status"] == status
    assert "type" in body
    assert "title" in body
    assert "detail" in body
    assert "instance" in body

    if detail is not None:
        assert body["detail"] == detail
    if title is not None:
        assert body["title"] == title
    if problem_type is not None:
        assert body["type"] == problem_type

    return body
