-- Crear base de datos
CREATE DATABASE video_recorder_db;

-- Conectar a la base de datos
-- \c video_recorder_db;

-- Crear tabla para videos
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    video_base64 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration FLOAT DEFAULT 0.0,
    file_size INTEGER DEFAULT 0
);

-- Crear índice para mejorar búsquedas
CREATE INDEX idx_videos_created_at ON videos(created_at);
CREATE INDEX idx_videos_filename ON videos(filename);