"""
Run with: uvicorn app.main:app --reload --port 8001
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.models.face_engine import face_engine
from app.schemas.api import (
    ClusterUnassignedRequest, ClusterUnassignedResponse, FaceResult,
    HealthResponse, ProcessPhotoRequest, ProcessPhotoResponse,
)
from app.services.clustering import cluster_unassigned_pool, try_incremental_match
from app.services.crops import save_crop
from app.services.db import get_connection, insert_face, recompute_person_centroid
from app.services.detection import detect_and_embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    face_engine.load()
    yield


app = FastAPI(title="Face Pipeline Service", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=face_engine.is_loaded)


@app.post("/process-photo", response_model=ProcessPhotoResponse)
async def process_photo(req: ProcessPhotoRequest) -> ProcessPhotoResponse:
    try:
        detected_faces, filtered_out = detect_and_embed(req.photo_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    conn = get_connection()
    results: list[FaceResult] = []

    try:
        for face in detected_faces:
            crop_path = save_crop(face.crop, req.photo_id)

            match = try_incremental_match(conn, face.embedding, req.project_id)
            person_id, confidence = (match[0], match[1]) if match else (None, None)

            face_id = insert_face(
                conn,
                photo_id=req.photo_id,
                bbox=face.bbox,
                crop_path=crop_path,
                det_score=face.det_score,
                embedding=face.embedding,
                person_id=person_id,
                blur_score=face.blur_score,
            )

            if person_id is not None:
                recompute_person_centroid(conn, person_id)

            results.append(FaceResult(
                face_id=face_id,
                bbox=face.bbox,
                crop_path=crop_path,
                det_score=face.det_score,
                person_id=person_id,
                match_confidence=confidence,
            ))
    finally:
        conn.close()

    return ProcessPhotoResponse(
        photo_id=req.photo_id,
        faces_detected=len(detected_faces) + filtered_out,
        faces_filtered_out=filtered_out,
        faces=results,
    )


@app.post("/cluster-unassigned", response_model=ClusterUnassignedResponse)
async def cluster_unassigned(req: ClusterUnassignedRequest) -> ClusterUnassignedResponse:
    conn = get_connection()
    try:
        summary = cluster_unassigned_pool(conn, req.project_id)
    finally:
        conn.close()

    return ClusterUnassignedResponse(**summary)
