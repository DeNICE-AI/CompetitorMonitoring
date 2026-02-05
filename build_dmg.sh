#!/usr/bin/env bash
set -euo pipefail

APP_NAME="CompetitorMonitoring"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
DMG_PATH="${DIST_DIR}/${APP_NAME}.dmg"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "App not found at ${APP_PATH}. Run build_app.sh first."
  exit 1
fi

if [[ -f "${DMG_PATH}" ]]; then
  rm -f "${DMG_PATH}"
fi

hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_PATH}" -ov -format UDZO "${DMG_PATH}"
