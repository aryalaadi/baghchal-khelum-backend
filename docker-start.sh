#!/bin/bash

# Wait for postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h postgres -p 5432 -U postgres; do
  sleep 1
done

echo "PostgreSQL is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting the application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
