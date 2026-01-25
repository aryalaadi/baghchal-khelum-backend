#!/bin/sh
set -e

# Wait for Postgres to be ready (optional, but safe)
until pg_isready -h postgres -U postgres; do
  echo "Waiting for postgres..."
  sleep 2
done

# Run Alembic only if flag file doesn't exist
if [ ! -f /app/.alembic_ran ]; then
  echo "Running Alembic migrations for the first time..."
  alembic upgrade head
  touch /app/.alembic_ran
fi

# Start FastAPI
exec uvicorn main:app --host 0.0.0.0 --port 8000
