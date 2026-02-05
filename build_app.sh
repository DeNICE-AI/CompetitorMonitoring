#!/usr/bin/env bash
set -euo pipefail

APP_NAME="CompetitorMonitoring"
PYTHON_BIN="${PYTHON_BIN:-python3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"

PYTHONPATH="${SCRIPT_DIR}" PYTHONNOUSERSITE=1 "${PYTHON_BIN}" -m PyInstaller \
  --clean \
  --noconfirm \
  --windowed \
  --paths "${SCRIPT_DIR}" \
  --name "${APP_NAME}" \
  --icon "${SCRIPT_DIR}/assets/app_icon.icns" \
  --add-data "${SCRIPT_DIR}/fastapi_app:fastapi_app" \
  --add-data "${SCRIPT_DIR}/history.json:." \
  --add-data "${SCRIPT_DIR}/certs:certs" \
  "${SCRIPT_DIR}/main.py"
