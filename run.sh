#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f database/logistics_analytics.db ]]; then
  python scripts/generate_data.py
  python scripts/load_database.py
fi
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT
npm --prefix frontend run dev -- --host 0.0.0.0
