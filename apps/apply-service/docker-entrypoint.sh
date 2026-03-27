#!/bin/sh
set -eu

DISPLAY_NUM="${DISPLAY_NUM:-99}"
SCREEN_GEOMETRY="${SCREEN_GEOMETRY:-1600x900x24}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

if [ "${BROWSER_HEADLESS:-true}" = "false" ]; then
  export DISPLAY=":${DISPLAY_NUM}"

  Xvfb "${DISPLAY}" -screen 0 "${SCREEN_GEOMETRY}" >/tmp/xvfb.log 2>&1 &
  fluxbox >/tmp/fluxbox.log 2>&1 &
  x11vnc -display "${DISPLAY}" -forever -shared -nopw -rfbport "${VNC_PORT}" >/tmp/x11vnc.log 2>&1 &
  websockify --web=/usr/share/novnc/ "${NOVNC_PORT}" "127.0.0.1:${VNC_PORT}" >/tmp/novnc.log 2>&1 &
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${SERVICE_PORT:-8000}"
