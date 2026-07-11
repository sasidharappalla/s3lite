import pytest
from pydantic import ValidationError

from app.schemas import BucketCreate, PresignRequest
from app.storage import object_locator


def test_bucket_name_length_validation() -> None:
    assert BucketCreate(name="documents").name == "documents"

    with pytest.raises(ValidationError):
        BucketCreate(name="ab")


@pytest.mark.parametrize("method", ["GET", "PUT"])
def test_presign_request_accepts_supported_methods(method: str) -> None:
    request = PresignRequest(method=method, expires_in=60)
    assert request.method == method


def test_presign_request_rejects_invalid_method() -> None:
    with pytest.raises(ValidationError):
        PresignRequest(method="DELETE", expires_in=60)


def test_object_locator_namespaces_and_normalizes_key() -> None:
    assert object_locator("documents", "/reports/annual.pdf") == ("documents/reports/annual.pdf")
