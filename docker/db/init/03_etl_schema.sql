CREATE SCHEMA IF NOT EXISTS etl;

-- ==========================
-- Enums del ETL
-- ==========================

CREATE TYPE etl.run_status_enum AS ENUM (
    'running',
    'success',
    'failed',
    'partial'
);

CREATE TYPE etl.match_status_enum AS ENUM (
    'pending',
    'running',
    'success',
    'skipped',
    'error'
);

CREATE TYPE etl.stage_enum AS ENUM (
    'discovery',
    'dimensions',
    'facts',
    'analytics'
);

-- ==========================
-- Tabla principal de runs
-- ==========================

CREATE TABLE etl.run (
    run_id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at      timestamptz NOT NULL DEFAULT now(),
    finished_at     timestamptz,
    status          etl.run_status_enum NOT NULL DEFAULT 'running',
    trigger_source  text NOT NULL DEFAULT 'manual',
    etl_version     text,
    source_context  jsonb,
    matches_discovered      integer NOT NULL DEFAULT 0,
    matches_processed_ok    integer NOT NULL DEFAULT 0,
    matches_processed_error integer NOT NULL DEFAULT 0,
    matches_skipped         integer NOT NULL DEFAULT 0,
    error_summary   text,
    note            text
);

CREATE INDEX idx_etl_run_status_started_at
    ON etl.run (status, started_at);

-- ==========================
-- Estado por partido
-- ==========================

CREATE TABLE etl.run_match (
    run_match_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          integer NOT NULL REFERENCES etl.run(run_id) ON DELETE CASCADE,
    match_id        integer NOT NULL,
    stage           etl.stage_enum NOT NULL DEFAULT 'discovery',
    status          etl.match_status_enum NOT NULL DEFAULT 'pending',
    tries           integer NOT NULL DEFAULT 0,
    error_code      text,
    error_message   text,
    started_at      timestamptz,
    finished_at     timestamptz,
    rows_inserted_core       integer NOT NULL DEFAULT 0,
    rows_updated_core        integer NOT NULL DEFAULT 0,
    rows_inserted_stats      integer NOT NULL DEFAULT 0,
    rows_updated_stats       integer NOT NULL DEFAULT 0,
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_etl_run_match UNIQUE (run_id, match_id)
);

CREATE INDEX idx_etl_run_match_match
    ON etl.run_match (match_id);

CREATE INDEX idx_etl_run_match_run_status
    ON etl.run_match (run_id, status);

CREATE INDEX idx_etl_run_match_status
    ON etl.run_match (status);

-- ==========================
-- Log de errores
-- ==========================

CREATE TABLE etl.error_log (
    error_id      integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id        integer REFERENCES etl.run(run_id) ON DELETE CASCADE,
    run_match_id  integer REFERENCES etl.run_match(run_match_id) ON DELETE CASCADE,
    match_id      integer,
    stage         etl.stage_enum,
    created_at    timestamptz NOT NULL DEFAULT now(),
    message       text NOT NULL,
    detail        text,
    context       jsonb
);

CREATE INDEX idx_etl_error_log_run
    ON etl.error_log (run_id);

CREATE INDEX idx_etl_error_log_match
    ON etl.error_log (match_id);

CREATE INDEX idx_etl_error_log_stage
    ON etl.error_log (stage);

-- ==========================
-- Checkpoints
-- ==========================

CREATE TABLE etl.checkpoint (
    checkpoint_name   text PRIMARY KEY,
    last_value        text NOT NULL,
    updated_at        timestamptz NOT NULL DEFAULT now(),
    note              text
);

-- ==========================
-- Lock simple para evitar dos ETL
-- ==========================

CREATE TABLE etl.lock (
    lock_name   text PRIMARY KEY,
    acquired_at timestamptz NOT NULL DEFAULT now(),
    run_id      integer REFERENCES etl.run(run_id) ON DELETE CASCADE,
    owner       text
);

-- ==========================
-- Funciones utilitarias
-- ==========================

CREATE OR REPLACE FUNCTION etl.start_run(
    p_trigger_source text DEFAULT 'manual',
    p_etl_version    text DEFAULT NULL,
    p_source_context jsonb DEFAULT NULL,
    p_note           text DEFAULT NULL
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id integer;
BEGIN
    INSERT INTO etl.run (trigger_source, etl_version, source_context, note)
    VALUES (p_trigger_source, p_etl_version, p_source_context, p_note)
    RETURNING run_id INTO v_run_id;

    RETURN v_run_id;
END;
$$;

CREATE OR REPLACE FUNCTION etl.finish_run(
    p_run_id        integer,
    p_status        etl.run_status_enum,
    p_error_summary text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE etl.run
    SET
        status        = p_status,
        finished_at   = now(),
        error_summary = p_error_summary
    WHERE run_id = p_run_id;
END;
$$;

CREATE OR REPLACE FUNCTION etl.register_match_status(
    p_run_id          integer,
    p_match_id        integer,
    p_stage           etl.stage_enum,
    p_status          etl.match_status_enum,
    p_error_code      text DEFAULT NULL,
    p_error_message   text DEFAULT NULL,
    p_rows_ins_core   integer DEFAULT 0,
    p_rows_upd_core   integer DEFAULT 0,
    p_rows_ins_stats  integer DEFAULT 0,
    p_rows_upd_stats  integer DEFAULT 0,
    p_set_started_at  boolean DEFAULT FALSE,
    p_set_finished_at boolean DEFAULT FALSE
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO etl.run_match (
        run_id, match_id, stage, status,
        error_code, error_message,
        rows_inserted_core, rows_updated_core,
        rows_inserted_stats, rows_updated_stats,
        started_at, finished_at
    )
    VALUES (
        p_run_id, p_match_id, p_stage, p_status,
        p_error_code, p_error_message,
        p_rows_ins_core, p_rows_upd_core,
        p_rows_ins_stats, p_rows_upd_stats,
        CASE WHEN p_set_started_at THEN now() ELSE NULL END,
        CASE WHEN p_set_finished_at THEN now() ELSE NULL END
    )
    ON CONFLICT (run_id, match_id)
    DO UPDATE
    SET
        stage               = EXCLUDED.stage,
        status              = EXCLUDED.status,
        error_code          = EXCLUDED.error_code,
        error_message       = EXCLUDED.error_message,
        rows_inserted_core  = EXCLUDED.rows_inserted_core,
        rows_updated_core   = EXCLUDED.rows_updated_core,
        rows_inserted_stats = EXCLUDED.rows_inserted_stats,
        rows_updated_stats  = EXCLUDED.rows_updated_stats,
        started_at          = COALESCE(etl.run_match.started_at,
                                       EXCLUDED.started_at),
        finished_at         = COALESCE(EXCLUDED.finished_at,
                                       etl.run_match.finished_at),
        last_updated_at     = now();
END;
$$;
