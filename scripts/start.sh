#!/bin/bash
set -e

# Apply wait-for-it pattern to wait for postgres
echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h "$POSTGRES_SERVER" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
    sleep 1
done

echo "Running migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
