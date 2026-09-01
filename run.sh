#!/bin/sh
# Resolve relative to this script, not the caller's cwd -- the preview launcher runs it
# from the workspace root. PD_TODAY pins "now" so the fixture always shows all three outcomes.
cd "$(dirname "$0")" || exit 1
export PYTHONPATH=src PD_TODAY=2026-09-01
exec ./.venv/bin/python -m uvicorn pending_delete.app:app --port 8077
