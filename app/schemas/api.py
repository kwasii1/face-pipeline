"""
Request/response contracts between Laravel and this service.
"""
from pydantic import BaseModel


class ProcessPhotoRequest(BaseModel):
    photo_id: int
    photo_path: str  # absolute path on disk, readable by this service


class FaceResult(BaseModel):
    face_id: int
    bbox: list[int]  # [x, y, width, height]
    crop_path: str
    det_score: float
    person_id: int | None
    match_confidence: float | None = None


class ProcessPhotoResponse(BaseModel):
    photo_id: int
    faces_detected: int
    faces_filtered_out: int
    faces: list[FaceResult]


class ClusterUnassignedResponse(BaseModel):
    faces_considered: int
    clusters_found: int
    noise_count: int
    cluster_ids: list[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool