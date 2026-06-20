"""Saves face crop thumbnails to disk for the review UI to display."""
import os
import uuid

import cv2
import numpy as np

from app.config import settings


def save_crop(crop: np.ndarray, photo_id: str) -> str:
    os.makedirs(settings.face_crops_dir, exist_ok=True)
    filename = f"{photo_id}_{uuid.uuid4().hex[:8]}.jpg"
    full_path = os.path.join(settings.face_crops_dir, filename)
    cv2.imwrite(full_path, crop)
    return filename
