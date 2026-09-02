#!/bin/sh
cd "$(dirname "$0")" || exit 1
set -a; . ./.env 2>/dev/null; set +a
export PYTHONPATH=src GOOGLE_CLOUD_PROJECT=nightshift-agentic-2026
exec ./.venv/bin/python -m uvicorn doppel.app:app --port 8077
