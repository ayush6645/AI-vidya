#!/bin/bash
gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:${PORT:-8080} --timeout 600
