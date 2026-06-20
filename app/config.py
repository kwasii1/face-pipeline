"""
Central configuration, loaded from environment variables / .env file.
Keeps tunable thresholds in one place instead of scattered magic numbers.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://postgres:password@localhost:5432/face_pipeline"

    # --- InsightFace model ---
    insightface_model_name: str = "buffalo_l"
    detection_size: tuple[int, int] = (640, 640)

    # --- Detection filtering ---
    min_detection_score: float = 0.5
    min_face_size_px: int = 40

    # --- Incremental matching ---
    match_confidence_threshold: float = 0.62

    # --- HDBSCAN clustering ---
    hdbscan_min_cluster_size: int = 2
    hdbscan_min_samples: int = 2
    hdbscan_metric: str = "euclidean"

    # --- Storage ---
    face_crops_dir: str = "./storage/face_crops"

    class Config:
        env_file = ".env"
        env_prefix = "FACE_PIPELINE_"


settings = Settings()