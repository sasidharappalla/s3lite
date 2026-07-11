<div align="center">

# ☁️ S3-lite Object Storage

### A Lightweight S3-Compatible Object Storage Service

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![MinIO](https://img.shields.io/badge/MinIO-C72E49?style=for-the-badge&logo=minio&logoColor=white)](https://min.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://github.com/sasidharappalla/s3lite/actions/workflows/ci.yml/badge.svg)](https://github.com/sasidharappalla/s3lite/actions/workflows/ci.yml)

<p align="center">
  <strong>S3-Compatible API</strong> · <strong>Presigned URLs</strong> · <strong>SHA-256 Integrity</strong> · <strong>1,000+ Concurrent Ops</strong>
</p>

---

</div>

## 🎯 What is S3-lite?

S3-lite is a **local Storage-as-a-Service** stack that implements core AWS S3 functionality. It uses PostgreSQL for bucket/object metadata management and MinIO as an S3-compatible blob store — all packaged as a single `docker compose up` deployment.

Perfect for local development, testing S3 integrations, or learning how object storage systems work under the hood.

## 🏗️ Architecture

```
┌──────────────┐        ┌──────────────────┐
│   Client     │───────▶│   FastAPI Server  │
│  (REST API)  │        │   (S3-lite Core)  │
└──────────────┘        └────────┬──────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
              ┌─────▼──────┐          ┌──────▼───────┐
              │ PostgreSQL  │          │    MinIO      │
              │  Metadata   │          │  Blob Store   │
              │             │          │ (S3-compat.)  │
              │ • Buckets   │          │               │
              │ • Objects   │          │ • Binary data │
              │ • API Keys  │          │ • Versioning  │
              └─────────────┘          └──────────────┘
```

## ✨ Features

### Storage Operations
- **Bucket management** — create, list, delete buckets
- **Object CRUD** — upload, download, list, delete objects with prefix filtering
- **Safe overwrite semantics** — version-aware object replacement
- **ETag & HEAD metadata** — standard S3-compatible object metadata

### Security
- **API-key authentication** — secure access control for all endpoints
- **HMAC presigned URLs** — time-bound GET/PUT URLs for temporary access
- **SHA-256 integrity checks** — content validation on every upload
- **Zero unauthorized access** incidents during load testing

### Infrastructure
- **Docker Compose** — single-command deployment of all services
- **PostgreSQL** — structured metadata with ACID guarantees
- **MinIO** — battle-tested S3-compatible object storage backend
- **1,000+ concurrent operations** supported

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/sasidharappalla/s3lite.git
cd s3lite

# Create local-only credentials and replace every placeholder value
cp .env.example .env

# Start everything
docker compose up --build

# API available at http://localhost:8001
# API Docs at http://localhost:8001/docs
# MinIO Console at http://localhost:9001
```

### Example Usage

```bash
# Create a bucket
curl -X POST http://localhost:8001/buckets \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket"}'

# Upload an object
curl -X PUT http://localhost:8001/buckets/my-bucket/objects/hello.txt \
  -H "X-API-Key: your-api-key" \
  -F "file=@hello.txt"

# Generate a presigned URL (time-bound)
curl -X POST http://localhost:8001/buckets/my-bucket/objects/hello.txt/presign \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"method": "GET", "expires_in": 3600}'
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Server** | FastAPI, Python | REST API layer |
| **Metadata DB** | PostgreSQL | Bucket & object metadata |
| **Blob Store** | MinIO | S3-compatible binary storage |
| **Auth** | API Keys + HMAC | Access control & presigned URLs |
| **Integrity** | SHA-256 | Content validation |
| **Deployment** | Docker Compose | Container orchestration |

## Load Test

The 1,000-concurrent-operations figure is a project-reported result. The
repository includes a k6 scenario that recreates the stated concurrency target:

```bash
S3LITE_API_KEY=your-api-key k6 run benchmarks/load.js
```

Commit the generated k6 summary alongside the environment details before using
the figure as independently reproducible benchmark evidence.

## 📁 Project Structure

```
s3lite/
├── .env.example
├── .github/workflows/ci.yml
├── app/
│   ├── main.py               # API routes and integrity checks
│   ├── auth.py               # API-key and presigned URL validation
│   ├── db.py                 # PostgreSQL session and startup checks
│   ├── models.py             # SQLAlchemy bucket/object models
│   ├── schemas.py            # Pydantic API schemas
│   └── storage.py            # MinIO client and object mapping
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── tests/
├── benchmarks/load.js
├── LICENSE
└── README.md
```

## Verification

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
ruff check app tests
ruff format --check app tests
pytest
```

GitHub Actions runs the same lint and test commands on Python 3.12 and 3.14.

## 📄 License

MIT License

---

<div align="center">
  <p>Built with ❤️ by <a href="https://github.com/sasidharappalla">Sasidhar Appalla</a></p>
</div>
