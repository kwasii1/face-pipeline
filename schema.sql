CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS photo_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    total_photos INTEGER NOT NULL,
    processed_photos INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(255) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES photo_batches(id) ON DELETE SET NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    path VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS faces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    cluster_id VARCHAR(255),
    bbox JSON NOT NULL,
    crop_path VARCHAR(255) NOT NULL,
    det_score DOUBLE PRECISION,
    embedding VECTOR(512),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS faces_embedding_hnsw_idx
    ON faces USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS faces_person_id_idx ON faces (person_id);
CREATE INDEX IF NOT EXISTS faces_cluster_id_idx ON faces (cluster_id);
CREATE INDEX IF NOT EXISTS faces_photo_id_idx ON faces (photo_id);

CREATE TABLE IF NOT EXISTS person_centroids (
    person_id UUID PRIMARY KEY REFERENCES people(id) ON DELETE CASCADE,
    centroid VECTOR(512),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS person_centroids_hnsw_idx
    ON person_centroids USING hnsw (centroid vector_cosine_ops);
