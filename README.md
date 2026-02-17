# S3-lite

A lightweight, S3-compatible object storage service built with FastAPI, PostgreSQL, and MinIO.

## Features

- **S3-Compatible Storage**: Uses MinIO for reliable object storage.
- **Metadata Management**: Stores object metadata (size, content type, checksum) in PostgreSQL.
- **Presigned URLs**: Securely upload and download objects using presigned URLs.
- **Dockerized**: Easy setup and deployment using Docker Compose.

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL
- **Object Storage**: MinIO
- **Containerization**: Docker & Docker Compose

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/sasidharappalla/s3lite.git
    cd s3lite
    ```

2.  **Start the services:**

    ```bash
    docker-compose up -d
    ```

    This will start the API, PostgreSQL database, and MinIO server.

3.  **Verify the services are running:**

    The API will be available at `http://localhost:8001`.
    You can check the health endpoint:

    ```bash
    curl http://localhost:8001/health
    ```

    Response:
    ```json
    {"status": "ok"}
    ```

## Configuration

The application is configured via environment variables. The defaults in `docker-compose.yml` are suitable for local development.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://s3lite:s3lite@db:5432/s3lite` |
| `MINIO_ENDPOINT` | MinIO server URL | `http://minio:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `MINIO_BUCKET` | Default bucket name | `s3lite` |
| `S3LITE_API_KEY` | API Key for authentication | `devkey` |
| `PRESIGN_SECRET` | Secret for signing URLs | `supersecret123` |
| `PUBLIC_BASE_URL` | Base URL for public access | `http://127.0.0.1:8001` |

## Usage

### Authentication
Most endpoints require the `X-API-Key` header with the value configured in `S3LITE_API_KEY` (default: `devkey`).

### Create a Bucket

```bash
curl -X POST "http://localhost:8001/buckets" \
  -H "X-API-Key: devkey" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket"}'
```

### Upload an Object (via Presigned URL)

1.  **Get a presigned upload URL:**

    ```bash
    curl -X POST "http://localhost:8001/buckets/my-bucket/objects/my-file.txt/presign" \
      -H "X-API-Key: devkey" \
      -H "Content-Type: application/json" \
      -d '{"method": "PUT", "expires_in": 3600, "content_type": "text/plain"}'
    ```

2.  **Upload the file using the returned URL:**

    ```bash
    curl -X PUT "<presigned_url_from_step_1>" \
      -H "Content-Type: text/plain" \
      -d "Hello, S3-lite!"
    ```

### List Objects

```bash
curl -X GET "http://localhost:8001/buckets/my-bucket/objects" \
  -H "X-API-Key: devkey"
```

### Download an Object

```bash
curl -X GET "http://localhost:8001/buckets/my-bucket/objects/my-file.txt" \
  -H "X-API-Key: devkey"
```
