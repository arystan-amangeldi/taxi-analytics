CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.file_loads (
    source_file TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    row_count BIGINT NOT NULL CHECK (row_count > 0),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);