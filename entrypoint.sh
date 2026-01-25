#!/bin/sh

# Run Alembic only if "first_run" file doesn't exist
if [ ! -f /app/.alembic_ran ]; then
    echo "Running Alembic migrations for the first time..."
    alembic upgrade head
    touch /app/.alembic_ran
fi

# Start the FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 8000
