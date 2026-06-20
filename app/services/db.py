"""
Database access for faces/people/photos tables. Schema is owned by Laravel
migrations (see schema.sql) — this service only reads/writes rows.
"""
import uuid

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from app.config import settings


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(settings.database_url)
    register_vector(conn)
    return conn


def insert_face(
    conn: psycopg.Connection,
    photo_id: str,
    bbox: list[int],
    crop_path: str,
    det_score: float,
    embedding: np.ndarray,
    person_id: str | None,
) -> str:
    face_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO faces (id, photo_id, bbox, crop_path, det_score, embedding, person_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now(), now())
            RETURNING id
            """,
            (face_id, photo_id, psycopg.types.json.Json(bbox), crop_path, det_score, embedding, person_id),
        )
        row = cur.fetchone()
        conn.commit()
        return str(row[0])


def find_best_person_match(
    conn: psycopg.Connection, embedding: np.ndarray, project_id: str,
) -> tuple[str, float] | None:
    """
    Compare a new face embedding against each Person's centroid within the
    given project. Returns (person_id, similarity) or None.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT pc.person_id, 1 - (pc.centroid <=> %s) AS similarity
            FROM person_centroids pc
            JOIN people p ON p.id = pc.person_id
            WHERE p.project_id = %s
              AND pc.centroid IS NOT NULL
            ORDER BY pc.centroid <=> %s
            LIMIT 1
            """,
            (embedding, project_id, embedding),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return str(row[0]), float(row[1])


def recompute_person_centroid(conn: psycopg.Connection, person_id: str) -> None:
    """
    Recompute and upsert a person's centroid (mean embedding of all their
    tagged faces). Call whenever a face is newly tagged to a person.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT embedding FROM faces WHERE person_id = %s AND embedding IS NOT NULL",
            (person_id,),
        )
        embeddings = [row[0] for row in cur.fetchall()]
        if not embeddings:
            cur.execute(
                "DELETE FROM person_centroids WHERE person_id = %s",
                (person_id,),
            )
            conn.commit()
            return
        centroid = np.mean(np.stack(embeddings), axis=0)
        centroid = centroid / np.linalg.norm(centroid)

        cur.execute(
            """
            INSERT INTO person_centroids (person_id, centroid, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (person_id)
            DO UPDATE SET centroid = EXCLUDED.centroid, updated_at = now()
            """,
            (person_id, centroid),
        )
        conn.commit()


def fetch_unassigned_face_embeddings(
    conn: psycopg.Connection, project_id: str,
) -> list[tuple[str, np.ndarray]]:
    """Fetch (face_id, embedding) for every face with no person_id and no
    cluster_id, within the given project."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT f.id, f.embedding
            FROM faces f
            JOIN photos p ON p.id = f.photo_id
            WHERE f.person_id IS NULL
              AND f.cluster_id IS NULL
              AND f.embedding IS NOT NULL
              AND p.project_id = %s
            """,
            (project_id,),
        )
        return [(str(row[0]), row[1]) for row in cur.fetchall()]


def write_cluster_ids(conn: psycopg.Connection, face_id_to_cluster: dict[str, str]) -> None:
    with conn.cursor() as cur:
        for face_id, cluster_id in face_id_to_cluster.items():
            cur.execute(
                "UPDATE faces SET cluster_id = %s, updated_at = now() WHERE id = %s",
                (cluster_id, face_id),
            )
        conn.commit()
