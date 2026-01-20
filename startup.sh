#!/bin/bash
echo "Starting deployment script..."
echo "Current Directory: $(pwd)"
echo "Listing Directory: $(ls -F)"
echo "Environment PORT: $PORT"

# Ensure we bind to the correct port provided by Cloud Run, defaulting to 8080 if not set
PORT=${PORT:-8080}

echo "Starting Gunicorn on port $PORT..."
# exec replaces the shell with gunicorn process, maintaining signal handling
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:$PORT --timeout 120 --log-level debug --access-logfile - --error-logfile -
