"""
Incremental matching against existing tagged people, plus HDBSCAN batch
clustering of the unreviewed face pool.
"""
import logging
import uuid

import numpy as np
import psycopg
from sklearn.cluster import HDBSCAN

from app.config import settings
from app.services.db import fetch_unassigned_face_embeddings, find_best_person_match, write_cluster_ids

logger = logging.getLogger(__name__)


def try_incremental_match(
    conn: psycopg.Connection, embedding: np.ndarray
) -> tuple[int, float] | None:
    result = find_best_person_match(conn, embedding)
    if result is None:
        return None

    person_id, similarity = result
    if similarity >= settings.match_confidence_threshold:
        return person_id, similarity

    return None


def cluster_unassigned_pool(conn: psycopg.Connection) -> dict:
    rows = fetch_unassigned_face_embeddings(conn)

    if len(rows) < settings.hdbscan_min_cluster_size:
        return {
            "faces_considered": len(rows),
            "clusters_found": 0,
            "noise_count": len(rows),
            "cluster_ids": [],
        }

    face_ids = [r[0] for r in rows]
    embeddings = np.stack([r[1] for r in rows])

    clusterer = HDBSCAN(
        min_cluster_size=settings.hdbscan_min_cluster_size,
        min_samples=settings.hdbscan_min_samples,
        metric=settings.hdbscan_metric,
    )
    labels = clusterer.fit_predict(embeddings)

    label_to_uuid: dict[int, str] = {}
    face_id_to_cluster: dict[int, str] = {}

    for face_id, label in zip(face_ids, labels):
        if label == -1:
            continue
        if label not in label_to_uuid:
            label_to_uuid[label] = str(uuid.uuid4())
        face_id_to_cluster[face_id] = label_to_uuid[label]

    if face_id_to_cluster:
        write_cluster_ids(conn, face_id_to_cluster)

    noise_count = int(np.sum(labels == -1))

    logger.info(
        "Clustered %d unassigned faces into %d clusters (%d noise)",
        len(rows), len(label_to_uuid), noise_count,
    )

    return {
        "faces_considered": len(rows),
        "clusters_found": len(label_to_uuid),
        "noise_count": noise_count,
        "cluster_ids": list(label_to_uuid.values()),
    }