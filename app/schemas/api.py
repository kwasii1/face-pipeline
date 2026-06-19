"""
Request/response contracts between Laravel and this service.
"""
from pydantic import BaseModel


class ProcessPhotoRequest(BaseModel):
    project_id: str
    photo_id: str
    photo_path: str  # absolute path on disk, readable by this service


class FaceResult(BaseModel):
    face_id: str
    bbox: list[int]  # [x, y, width, height]
    crop_path: str
    det_score: float
    person_id: str | None
    match_confidence: float | None = None


class ProcessPhotoResponse(BaseModel):
    photo_id: str
    faces_detected: int
    faces_filtered_out: int
    faces: list[FaceResult]


class ClusterUnassignedRequest(BaseModel):
    project_id: str


class ClusterUnassignedResponse(BaseModel):
    faces_considered: int
    clusters_found: int
    noise_count: int
    cluster_ids: list[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
