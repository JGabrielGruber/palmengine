#!/bin/sh
set -eu

DATA_DIR="${PALM_DATA_DIR:-/data}"
LOG_FILE="${PALM_LOG_FILE:-/var/log/palm/palm.log}"
HOST="${PALM_SERVER_HOST:-0.0.0.0}"
PORT="${PALM_SERVER_PORT:-8080}"
BACKEND="${PALM_STORAGE_BACKEND:-filesystem}"

mkdir -p "${DATA_DIR}" "$(dirname "${LOG_FILE}")"

echo "Starting Palm server on ${HOST}:${PORT}"
echo "Storage: ${BACKEND} → ${DATA_DIR}"
echo "Log file: ${LOG_FILE}"

exec sh -c "palm \
  --storage-backend '${BACKEND}' \
  --data-dir '${DATA_DIR}' \
  host server \
  --host '${HOST}' \
  --port '${PORT}' \
  2>&1 | tee -a '${LOG_FILE}'"