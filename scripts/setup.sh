#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm ci --prefix frontend --cache "${PORTAL_NPM_CACHE:-/tmp/gayatri-npm-cache}"
.venv/bin/python -m scripts.seed_db
npm run build --prefix frontend
