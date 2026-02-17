import hmac
import hashlib
import os
import time
from typing import Optional

from fastapi import Header, HTTPException, Request

API_KEY = os.environ.get("S3LITE_API_KEY", "")
PRESIGN_SECRET = os.environ.get("PRESIGN_SECRET", "")

def _sign(method: str, path: str, expires: int, ct: str = "") -> str:
    msg = f"{method.upper()}\n{path}\n{expires}\n{ct}".encode("utf-8")
    secret = PRESIGN_SECRET.encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()

def validate_presign(request: Request, ct: str = "") -> None:
    if not PRESIGN_SECRET:
        raise HTTPException(status_code=500, detail="PRESIGN_SECRET not configured")

    qp = request.query_params
    sig = qp.get("sig")
    expires_str = qp.get("expires")
    signed_ct = qp.get("ct", "")

    if not sig or not expires_str:
        raise HTTPException(status_code=401, detail="Missing presign parameters")

    try:
        expires = int(expires_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid expires")

    now = int(time.time())
    if now > expires:
        raise HTTPException(status_code=401, detail="Presigned URL expired")

    if signed_ct and signed_ct != ct:
        raise HTTPException(status_code=401, detail="Content-Type mismatch for presigned URL")

    expected = _sign(request.method, request.url.path, expires, signed_ct)
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

def authorize(request: Request, x_api_key: Optional[str] = Header(default=None)) -> None:
    qp = request.query_params
    if qp.get("sig") and qp.get("expires"):
        validate_presign(request, ct=qp.get("ct", ""))
        return

    if not API_KEY:
        raise HTTPException(status_code=500, detail="S3LITE_API_KEY not configured")

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
