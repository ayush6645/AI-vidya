#!/bin/bash
gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:8000 --timeout 600
