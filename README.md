# Face Pipeline

A microservice for face detection, recognition, and clustering built with FastAPI and InsightFace.

## Overview

- Detects faces in photos using the SCRFD detector
- Computes 512-dimensional ArcFace embeddings for each face
- Filters detections by confidence, size, and blur quality
- Matches faces against known people using vector similarity (pgvector)
- Clusters unassigned faces with HDBSCAN
- Stores results in PostgreSQL with pgvector for fast cosine similarity search

## Tech Stack

- **Python 3.12** with **FastAPI** and **Uvicorn**
- **InsightFace** (ONNX Runtime) for face detection and recognition
- **PostgreSQL 15+** with **pgvector** extension
- **HDBSCAN** (scikit-learn) for clustering

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL 15+ with [pgvector](https://github.com/pgvector/pgvector) extension
- 4 GB+ RAM (models require significant memory)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kwasii1/face-pipeline.git
cd face-pipeline
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `FACE_PIPELINE_DATABASE_URL` | `postgresql://postgres:password@localhost:5432/face_pipeline` | PostgreSQL connection string |
| `FACE_PIPELINE_INSIGHTFACE_MODEL_NAME` | `buffalo_l` | InsightFace model pack |
| `FACE_PIPELINE_MIN_DETECTION_SCORE` | `0.5` | Minimum detection confidence |
| `FACE_PIPELINE_MIN_FACE_SIZE_PX` | `40` | Minimum face width/height (pixels) |
| `FACE_PIPELINE_MIN_RELATIVE_FACE_SIZE` | `0.015` | Minimum face size relative to image dimensions |
| `FACE_PIPELINE_MATCH_CONFIDENCE_THRESHOLD` | `0.62` | Cosine similarity threshold for person matching |
| `FACE_PIPELINE_HDBSCAN_MIN_CLUSTER_SIZE` | `2` | Minimum HDBSCAN cluster size |
| `FACE_PIPELINE_HDBSCAN_MIN_SAMPLES` | `2` | Minimum HDBSCAN samples |
| `FACE_PIPELINE_FACE_CROPS_DIR` | `./storage/face_crops` | Directory for face thumbnail crops |

### 4. Create database schema

Run `schema.sql` against your PostgreSQL database to create tables and indexes:

```bash
psql -h localhost -U postgres -d face_pipeline -f schema.sql
```

### 5. Run the service

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

On first startup, InsightFace downloads the `buffalo_l` model pack (~330 MB) to `~/.insightface/`.

The service will be available at `http://localhost:8001`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check with model load status |
| `POST` | `/process-photo` | Detect and match faces in a photo |
| `POST` | `/cluster-unassigned` | Cluster unreviewed faces for a project |

### `POST /process-photo`

```json
{
  "project_id": "uuid",
  "photo_id": "uuid",
  "photo_path": "/path/to/photo.jpg"
}
```

### `POST /cluster-unassigned`

```json
{
  "project_id": "uuid"
}
```

## Docker

### Build

```bash
docker build -t face-pipeline .
```

### Run

```bash
docker run -d \
  --name face-pipeline \
  -p 8001:8001 \
  -e FACE_PIPELINE_DATABASE_URL=postgresql://user:pass@host:5432/face_pipeline \
  -v /path/to/crops:/data/face_crops \
  ghcr.io/kwasii1/face-pipeline:latest
```

### Published Image

Images are built and published to `ghcr.io/kwasii1/face-pipeline` on every push to `main`, tagged with `latest` and the full git SHA.

```
docker pull ghcr.io/kwasii1/face-pipeline:latest
```

## Notes

- InsightFace models are pre-baked into the Docker image for instant startup.
- Database schema migrations are managed by the Laravel application.
- The service does not include authentication — place it behind a reverse proxy or API gateway.
