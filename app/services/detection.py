"""
Runs detection + embedding on an image, filtering out low-confidence
and too-small detections before they pollute the embedding space.
"""
import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.config import settings
from app.models.face_engine import face_engine
from app.services.quality import compute_blur_score

logger = logging.getLogger(__name__)


@dataclass
class DetectedFace:
    bbox: list[int]
    det_score: float
    embedding: np.ndarray
    crop: np.ndarray
    blur_score: float = 0.0


def detect_and_embed(image_path: str) -> tuple[list[DetectedFace], int]:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at {image_path}")

    raw_faces = face_engine.get_faces(image)

    kept: list[DetectedFace] = []
    filtered_out = 0

    for face in raw_faces:
        det_score = float(face.det_score)
        x1, y1, x2, y2 = face.bbox.astype(int)
        w, h = x2 - x1, y2 - y1

        if det_score < settings.min_detection_score:
            filtered_out += 1
            continue
        if max(w, h) < settings.min_face_size_px:
            filtered_out += 1
            continue

        embedding = face.embedding.astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        crop = image[max(0, y1):y2, max(0, x1):x2]
        blur_score = compute_blur_score(crop)

        kept.append(DetectedFace(
            bbox=[int(x1), int(y1), int(w), int(h)],
            det_score=det_score,
            embedding=embedding,
            crop=crop,
            blur_score=blur_score,
        ))

    return kept, filtered_out