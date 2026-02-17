import hashlib
import os
import tempfile
import time
import urllib.parse
import hmac
import hashlib as _hashlib

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import authorize
from .db import engine, get_db, wait_for_db
from .models import Base, Bucket, Object
from .schemas import BucketCreate, BucketOut, ObjectOut, PresignOut, PresignRequest
from .storage import MINIO_BUCKET, ensure_bucket_exists, object_locator, s3_client, wait_for_s3

PRESIGN_SECRET = os.environ.get("PRESIGN_SECRET", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

def _presign_sig(method: str, path: str, expires: int, ct: str = "") -> str:
    msg = f"{method.upper()}\n{path}\n{expires}\n{ct}".encode("utf-8")
    secret = PRESIGN_SECRET.encode("utf-8")
    return hmac.new(secret, msg, _hashlib.sha256).hexdigest()

app = FastAPI(title="S3-lite")

@app.on_event("startup")
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    wait_for_s3()
    ensure_bucket_exists()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/buckets", response_model=BucketOut, status_code=status.HTTP_201_CREATED)
def create_bucket(payload: BucketCreate, db: Session = Depends(get_db), _=Depends(authorize)):
    bucket = Bucket(name=payload.name)
    db.add(bucket)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bucket already exists")
    db.refresh(bucket)
    return bucket

@app.get("/buckets", response_model=list[BucketOut])
def list_buckets(db: Session = Depends(get_db), _=Depends(authorize)):
    return db.query(Bucket).order_by(Bucket.created_at.desc()).all()

@app.post("/buckets/{bucket_name}/objects/{object_key:path}/presign", response_model=PresignOut)
def presign_object(bucket_name: str, object_key: str, payload: PresignRequest, db: Session = Depends(get_db), _=Depends(authorize)):
    if not PRESIGN_SECRET:
        raise HTTPException(status_code=500, detail="PRESIGN_SECRET not configured")

    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).one_or_none()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    path = f"/buckets/{bucket_name}/objects/{object_key}"
    expires = int(time.time()) + payload.expires_in
    ct = payload.content_type or ""
    sig = _presign_sig(payload.method, path, expires, ct)

    params = {"expires": str(expires), "sig": sig}
    if ct:
        params["ct"] = ct

    url = f"{PUBLIC_BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    return PresignOut(url=url)

@app.put("/buckets/{bucket_name}/objects/{object_key:path}", response_model=ObjectOut)
async def upload_object(
    request: Request,
    bucket_name: str,
    object_key: str,
    overwrite: bool = True,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(authorize),
):
    signed_ct = request.query_params.get("ct", "")
    if signed_ct and (file.content_type or "") != signed_ct:
        raise HTTPException(status_code=401, detail="Content-Type mismatch for presigned URL")

    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).one_or_none()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    existing = (
        db.query(Object)
        .filter(Object.bucket_id == bucket.id, Object.object_key == object_key)
        .one_or_none()
    )
    if existing is not None and not overwrite:
        raise HTTPException(status_code=409, detail="Object already exists (overwrite=false)")

    content_type = file.content_type or "application/octet-stream"
    sha = hashlib.sha256()
    size = 0

    with tempfile.NamedTemporaryFile() as tmp:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
            size += len(chunk)
            tmp.write(chunk)

        tmp.flush()
        tmp.seek(0)

        s3 = s3_client()
        locator = object_locator(bucket.name, object_key)
        s3.upload_fileobj(tmp, MINIO_BUCKET, locator, ExtraArgs={"ContentType": content_type})

    checksum = sha.hexdigest()

    if existing is None:
        obj = Object(
            bucket_id=bucket.id,
            object_key=object_key,
            size=size,
            checksum_sha256=checksum,
            content_type=content_type,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    existing.size = size
    existing.checksum_sha256 = checksum
    existing.content_type = content_type
    db.commit()
    db.refresh(existing)
    return existing

@app.get("/buckets/{bucket_name}/objects", response_model=list[ObjectOut])
def list_objects(bucket_name: str, db: Session = Depends(get_db), _=Depends(authorize)):
    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).one_or_none()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return (
        db.query(Object)
        .filter(Object.bucket_id == bucket.id)
        .order_by(Object.created_at.desc())
        .all()
    )

@app.head("/buckets/{bucket_name}/objects/{object_key:path}")
def head_object(bucket_name: str, object_key: str, db: Session = Depends(get_db), _=Depends(authorize)):
    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).one_or_none()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    obj = (
        db.query(Object)
        .filter(Object.bucket_id == bucket.id, Object.object_key == object_key)
        .one_or_none()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    headers = {
        "Content-Length": str(obj.size),
        "ETag": obj.checksum_sha256,
        "X-Checksum-Sha256": obj.checksum_sha256,
    }
    return Response(status_code=200, headers=headers)

@app.get("/buckets/{bucket_name}/objects/{object_key:path}")
def download_object(bucket_name: str, object_key: str, db: Session = Depends(get_db), _=Depends(authorize)):
    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).one_or_none()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    obj = (
        db.query(Object)
        .filter(Object.bucket_id == bucket.id, Object.object_key == object_key)
        .one_or_none()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    s3 = s3_client()
    locator = object_locator(bucket.name, object_key)
    resp = s3.get_object(Bucket=MINIO_BUCKET, Key=locator)
    body = resp["Body"]

    def iter_chunks():
        for chunk in body.iter_chunks(chunk_size=1024 * 1024):
            if chunk:
                yield chunk

    headers = {
        "Content-Length": str(obj.size),
        "ETag": obj.checksum_sha256,
        "X-Checksum-Sha256": obj.checksum_sha256,
    }
    return StreamingResponse(iter_chunks(), media_type=obj.content_type, headers=headers)

@app.delete("/buckets/{bucket_name}/objects/{object_key:path}", status_code=204)
def delete_object(bucket_name: str, object_key: str, db: Session = Depends(get_db), _=Depends(authorize)):
    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).one_or_none()
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")

    obj = (
        db.query(Object)
        .filter(Object.bucket_id == bucket.id, Object.object_key == object_key)
        .one_or_none()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    s3 = s3_client()
    locator = object_locator(bucket.name, object_key)
    s3.delete_object(Bucket=MINIO_BUCKET, Key=locator)

    db.delete(obj)
    db.commit()
    return None
