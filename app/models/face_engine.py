"""
Loads the InsightFace model pack (SCRFD detector + ArcFace recognizer) once.
Loaded at app startup via lifespan in main.py, reused for every request.
"""
import logging

from insightface.app import FaceAnalysis

from app.config import settings

logger = logging.getLogger(__name__)


class FaceEngine:
    def __init__(self) -> None:
        self._app: FaceAnalysis | None = None

    def load(self) -> None:
        logger.info("Loading InsightFace model pack: %s", settings.insightface_model_name)
        self._app = FaceAnalysis(
            name=settings.insightface_model_name,
            providers=["CPUExecutionProvider"],
            # Swap to ["CUDAExecutionProvider", "CPUExecutionProvider"] if you
            # have an NVIDIA GPU + CUDA installed.
        )
        self._app.prepare(ctx_id=0, det_size=settings.detection_size)
        logger.info("Model loaded.")

    @property
    def is_loaded(self) -> bool:
        return self._app is not None

    def get_faces(self, image):
        if self._app is None:
            raise RuntimeError("FaceEngine not loaded — call load() at startup.")
        return self._app.get(image)


face_engine = FaceEngine()