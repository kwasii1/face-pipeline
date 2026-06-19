CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS people (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS photo_batches (
    id BIGSERIAL PRIMARY KEY,
    total_photos INTEGER NOT NULL,
    processed_photos INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS photos (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT REFERENCES photo_batches(id) ON DELETE SET NULL,
    path VARCHAR(1024) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS faces (
    id BIGSERIAL PRIMARY KEY,
    photo_id BIGINT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    person_id BIGINT REFERENCES people(id) ON DELETE SET NULL,
    cluster_id VARCHAR(64),
    bbox JSONB NOT NULL,
    crop_path VARCHAR(1024) NOT NULL,
    det_score FLOAT NOT NULL,
    embedding VECTOR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS faces_embedding_hnsw_idx
    ON faces USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS faces_person_id_idx ON faces (person_id);
CREATE INDEX IF NOT EXISTS faces_cluster_id_idx ON faces (cluster_id);
CREATE INDEX IF NOT EXISTS faces_photo_id_idx ON faces (photo_id);

CREATE TABLE IF NOT EXISTS person_centroids (
    person_id BIGINT PRIMARY KEY REFERENCES people(id) ON DELETE CASCADE,
    centroid VECTOR(512) NOT NULL,
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS person_centroids_hnsw_idx
    ON person_centroids USING hnsw (centroid vector_cosine_ops);