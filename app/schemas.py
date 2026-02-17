from pydantic import BaseModel, Field

class BucketCreate(BaseModel):
    name: str = Field(min_length=3, max_length=63)

class BucketOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ObjectOut(BaseModel):
    id: int
    bucket_id: int
    object_key: str
    size: int
    checksum_sha256: str
    content_type: str

    class Config:
        from_attributes = True

class PresignRequest(BaseModel):
    method: str = Field(pattern="^(GET|PUT)$")
    expires_in: int = Field(ge=10, le=86400)  # 10s to 24h
    content_type: str | None = None

class PresignOut(BaseModel):
    url: str
