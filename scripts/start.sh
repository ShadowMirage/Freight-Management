#!/bin/sh
set -e

echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"

echo "Running Alembic migrations..."
if ! alembic upgrade head; then
    echo "CRITICAL: Alembic migrations failed!"
    exit 1
fi
echo "Alembic migrations completed successfully."

echo "Starting FastAPI Application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
