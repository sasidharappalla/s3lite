import time
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import auth


def make_request(method: str, path: str, query: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": urlencode(query).encode(),
            "headers": [],
            "client": ("test", 123),
            "server": ("test", 80),
            "root_path": "",
        }
    )


def test_valid_presigned_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "PRESIGN_SECRET", "test-signing-secret")
    path = "/buckets/demo/objects/report.pdf"
    expires = int(time.time()) + 60
    signature = auth._sign("GET", path, expires)
    request = make_request(
        "GET",
        path,
        {"expires": str(expires), "sig": signature},
    )

    auth.validate_presign(request)


@pytest.mark.parametrize(
    ("query", "detail"),
    [
        ({"expires": "not-a-number", "sig": "unused"}, "Invalid expires"),
        ({"expires": "1", "sig": "unused"}, "Presigned URL expired"),
    ],
)
def test_invalid_presigned_request(
    monkeypatch: pytest.MonkeyPatch,
    query: dict[str, str],
    detail: str,
) -> None:
    monkeypatch.setattr(auth, "PRESIGN_SECRET", "test-signing-secret")
    request = make_request("GET", "/buckets/demo/objects/report.pdf", query)

    with pytest.raises(HTTPException, match=detail) as exc_info:
        auth.validate_presign(request)

    assert exc_info.value.status_code == 401


def test_tampered_signature_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "PRESIGN_SECRET", "test-signing-secret")
    expires = int(time.time()) + 60
    request = make_request(
        "GET",
        "/buckets/demo/objects/report.pdf",
        {"expires": str(expires), "sig": "not-the-signature"},
    )

    with pytest.raises(HTTPException, match="Invalid signature") as exc_info:
        auth.validate_presign(request)

    assert exc_info.value.status_code == 401


def test_api_key_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "API_KEY", "test-api-key")
    request = make_request("GET", "/buckets", {})

    auth.authorize(request, x_api_key="test-api-key")

    with pytest.raises(HTTPException, match="Missing or invalid API key") as exc_info:
        auth.authorize(request, x_api_key="wrong-key")

    assert exc_info.value.status_code == 401
