#!/bin/sh
cd "$(dirname "$0")" || exit 1
export PYTHONPATH=src
exec ./.venv/bin/python -m uvicorn doppel.app:app --port 8077
