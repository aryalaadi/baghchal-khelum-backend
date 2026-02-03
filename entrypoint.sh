#!/bin/sh
set -e

# Configuration
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-bagchal}"
MAX_RETRIES="${DB_MAX_RETRIES:-30}"
RETRY_INTERVAL="${DB_RETRY_INTERVAL:-2}"
ENVIRONMENT="${ENVIRONMENT:-production}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Logging helper
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting entrypoint script..."
log "Environment: ${ENVIRONMENT}"

# Wait for Postgres to be ready with retry limit
retry_count=0
log "Waiting for PostgreSQL at ${POSTGRES_HOST}..."

until pg_isready -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -q; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $MAX_RETRIES ]; then
        log "ERROR: PostgreSQL not available after ${MAX_RETRIES} attempts. Exiting."
        exit 1
    fi
    log "PostgreSQL not ready yet (attempt ${retry_count}/${MAX_RETRIES}). Retrying in ${RETRY_INTERVAL}s..."
    sleep "${RETRY_INTERVAL}"
done

log "PostgreSQL is ready!"

# Run Alembic migrations
log "Running database migrations..."
if alembic upgrade head; then
    log "Database migrations completed successfully."
else
    log "ERROR: Database migrations failed!"
    exit 1
fi

# Start the application based on environment
if [ "${ENVIRONMENT}" = "development" ]; then
    log "Starting FastAPI in development mode with auto-reload..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level "${LOG_LEVEL}"
else
    log "Starting FastAPI in production mode with Gunicorn (${GUNICORN_WORKERS} workers)..."
    exec gunicorn main:app \
        --workers "${GUNICORN_WORKERS}" \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --access-logfile - \
        --error-logfile - \
        --capture-output \
        --log-level "${LOG_LEVEL}" \
        --timeout 120 \
        --keep-alive 5 \
        --graceful-timeout 30
fi
