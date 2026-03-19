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

# ── Gunicorn starten ────────────────────────────────────────────
# Versuche gevent-websocket Worker (für WebSocket-Support)
# Fallback auf Standard-sync Worker wenn nicht verfügbar
if python3 -c "import geventwebsocket" 2>/dev/null; then
  WORKER_CLASS="geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
  WORKERS="${GUNICORN_WORKERS:-1}"
  echo "[entrypoint] Starte mit GeventWebSocket-Worker"
elif python3 -c "import gevent" 2>/dev/null; then
  WORKER_CLASS="gevent"
  WORKERS="${GUNICORN_WORKERS:-2}"
  echo "[entrypoint] Starte mit Gevent-Worker (kein WebSocket)"
else
  WORKER_CLASS="sync"
  WORKERS="${GUNICORN_WORKERS:-2}"
  echo "[entrypoint] Starte mit Sync-Worker (kein WebSocket)"
fi

exec gunicorn \
  --bind 0.0.0.0:8000 \
  --worker-class "$WORKER_CLASS" \
  --workers "$WORKERS" \
  --timeout 120 \
  --access-logfile - \
  'app:create_app()'
