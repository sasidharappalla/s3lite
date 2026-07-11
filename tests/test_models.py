import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Bucket, Object


def test_bucket_name_is_unique() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Bucket(name="documents"))
        session.commit()
        session.add(Bucket(name="documents"))

        with pytest.raises(IntegrityError):
            session.commit()


def test_object_key_is_unique_within_bucket() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        bucket = Bucket(name="documents")
        session.add(bucket)
        session.flush()

        values = {
            "bucket_id": bucket.id,
            "object_key": "reports/annual.pdf",
            "size": 42,
            "checksum_sha256": "a" * 64,
            "content_type": "application/pdf",
        }
        session.add(Object(**values))
        session.commit()
        session.add(Object(**values))

        with pytest.raises(IntegrityError):
            session.commit()
