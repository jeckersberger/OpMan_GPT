#!/bin/sh
set -e

APP_DIR=/app
REPO="https://github.com/jeckersberger/OpMan_GPT.git"

# ── Git Pull beim Start (nur wenn User + Token gesetzt) ─────────
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_USER" ]; then
  echo "[entrypoint] GitHub-Zugang gesetzt – ziehe Updates aus main …"
  git config --global --add safe.directory "$APP_DIR"

  # Origin-URL mit User:Token setzen (privates Repo)
  git -C "$APP_DIR" remote set-url origin \
    "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/jeckersberger/OpMan_GPT.git"

  git -C "$APP_DIR" fetch origin main --quiet || echo "[entrypoint] WARNUNG: git fetch fehlgeschlagen"
  git -C "$APP_DIR" reset --hard origin/main   || echo "[entrypoint] WARNUNG: git reset fehlgeschlagen"

  echo "[entrypoint] Git-Update abgeschlossen."
else
  echo "[entrypoint] GITHUB_USER oder GITHUB_TOKEN nicht gesetzt – überspringe Git-Update."
fi

# ── pip install falls requirements sich geändert haben ──────────
# (optional, nur wenn venv vorhanden)
if [ -x "$APP_DIR/venv/bin/pip" ]; then
  "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt" 2>/dev/null || true
fi

# ── Gunicorn starten (gevent-websocket für SocketIO) ──────────
exec gunicorn \
  --bind 0.0.0.0:8000 \
  --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
  --workers "${GUNICORN_WORKERS:-1}" \
  --timeout 120 \
  --access-logfile - \
  'app:create_app()'
