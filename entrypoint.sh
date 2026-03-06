#!/bin/sh
set -e

APP_DIR=/app
REPO="https://github.com/jeckersberger/OpMan_GPT.git"

# ── Git Pull beim Start (nur wenn Token gesetzt) ────────────────
if [ -n "$GITHUB_TOKEN" ]; then
  echo "[entrypoint] GITHUB_TOKEN gesetzt – ziehe Updates aus main …"
  git config --global --add safe.directory "$APP_DIR"

  # Origin-URL mit Token setzen (privates Repo)
  git -C "$APP_DIR" remote set-url origin \
    "https://${GITHUB_TOKEN}@github.com/jeckersberger/OpMan_GPT.git"

  git -C "$APP_DIR" fetch origin main --quiet || echo "[entrypoint] WARNUNG: git fetch fehlgeschlagen"
  git -C "$APP_DIR" reset --hard origin/main   || echo "[entrypoint] WARNUNG: git reset fehlgeschlagen"

  echo "[entrypoint] Git-Update abgeschlossen."
else
  echo "[entrypoint] Kein GITHUB_TOKEN gesetzt – überspringe Git-Update."
fi

# ── pip install falls requirements sich geändert haben ──────────
# (optional, nur wenn venv vorhanden)
if [ -x "$APP_DIR/venv/bin/pip" ]; then
  "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt" 2>/dev/null || true
fi

# ── Gunicorn starten ────────────────────────────────────────────
exec gunicorn \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout 120 \
  --access-logfile - \
  'app:create_app()'
