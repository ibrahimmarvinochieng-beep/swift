CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS events (
    event_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type      TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    location        TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    severity        INTEGER CHECK (severity BETWEEN 1 AND 5),
    confidence_score DOUBLE PRECISION CHECK (confidence_score BETWEEN 0 AND 1),
    sources         TEXT[],
    raw_text        TEXT,
    entities        JSONB DEFAULT '{}',
    embedding_id    TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_location ON events(location);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_events_created ON events(created_at);
CREATE INDEX idx_events_confidence ON events(confidence_score);

CREATE TABLE IF NOT EXISTS raw_signals (
    signal_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type     TEXT NOT NULL,
    source_name     TEXT,
    content         TEXT NOT NULL,
    url             TEXT,
    fetched_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed       BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_signals_source ON raw_signals(source_type);
CREATE INDEX idx_signals_processed ON raw_signals(processed);

CREATE TABLE IF NOT EXISTS users (
    user_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT DEFAULT 'viewer' CHECK (role IN ('admin', 'analyst', 'viewer')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(user_id),
    action          TEXT NOT NULL,
    resource        TEXT,
    details         JSONB,
    ip_address      TEXT,
    timestamp       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
