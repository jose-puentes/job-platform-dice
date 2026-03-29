#!/bin/sh
set -eu

DISPLAY_NUM="${DISPLAY_NUM:-99}"
SCREEN_GEOMETRY="${SCREEN_GEOMETRY:-1600x900x24}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

if [ "${BROWSER_HEADLESS:-true}" = "false" ]; then
  export DISPLAY=":${DISPLAY_NUM}"
  LOCK_FILE="/tmp/.X${DISPLAY_NUM}-lock"
  SOCKET_DIR="/tmp/.X11-unix"
  SOCKET_FILE="${SOCKET_DIR}/X${DISPLAY_NUM}"

  rm -f "${LOCK_FILE}" "${SOCKET_FILE}"
  pkill -f "Xvfb ${DISPLAY}" >/dev/null 2>&1 || true
  pkill -f "x11vnc.*${VNC_PORT}" >/dev/null 2>&1 || true
  pkill -f "websockify.*${NOVNC_PORT}" >/dev/null 2>&1 || true
  mkdir -p "${SOCKET_DIR}"

  Xvfb "${DISPLAY}" -screen 0 "${SCREEN_GEOMETRY}" >/tmp/xvfb.log 2>&1 &

  DISPLAY_READY=0
  for _ in $(seq 1 20); do
    if [ -S "${SOCKET_FILE}" ]; then
      DISPLAY_READY=1
      break
    fi
    sleep 0.25
  done

  if [ "${DISPLAY_READY}" -ne 1 ]; then
    echo "Xvfb did not become ready on ${DISPLAY}" >&2
    tail -n 50 /tmp/xvfb.log >&2 || true
    exit 1
  fi

  fluxbox >/tmp/fluxbox.log 2>&1 &
  x11vnc -display "${DISPLAY}" -forever -shared -nopw -rfbport "${VNC_PORT}" >/tmp/x11vnc.log 2>&1 &
  websockify --web=/usr/share/novnc/ "${NOVNC_PORT}" "127.0.0.1:${VNC_PORT}" >/tmp/novnc.log 2>&1 &
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${SERVICE_PORT:-8000}"
