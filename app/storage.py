import os
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "s3lite")

_s3 = None

def s3_client():
    global _s3
    if _s3 is None:
        if not (MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY):
            raise RuntimeError("MinIO env vars not set (MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY)")
        _s3 = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
    return _s3

def wait_for_s3(max_attempts: int = 30, sleep_s: float = 1.0) -> None:
    last_exc = None
    s3 = s3_client()
    for _ in range(max_attempts):
        try:
            s3.list_buckets()
            return
        except Exception as exc:
            last_exc = exc
            time.sleep(sleep_s)
    raise RuntimeError(f"MinIO not ready after {max_attempts} attempts: {last_exc}")

def ensure_bucket_exists() -> None:
    s3 = s3_client()
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=MINIO_BUCKET)

def object_locator(bucket_name: str, object_key: str) -> str:
    # store everything inside ONE MinIO bucket, namespaced by logical bucket
    safe_key = object_key.lstrip("/")
    return f"{bucket_name}/{safe_key}"
