#!/bin/bash
# =============================================================================
# OpMan GPT – Update-Skript
# =============================================================================
# Zieht die neueste Version aus dem main-Branch und startet die App neu.
#
# Verwendung:
#   bash update.sh              # Bare-Metal (systemd/gunicorn)
#   bash update.sh --docker     # Docker-Deployment
# =============================================================================

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

MODE="bare"
[ "$1" = "--docker" ] && MODE="docker"

echo "=============================================="
echo "  OpMan GPT – Update aus main"
echo "  Modus: $MODE"
echo "=============================================="

# ── 1. Git Pull ──────────────────────────────────────────────────
echo "[1] Git pull origin main …"
git fetch origin main
git pull origin main
echo "    ✓ Code aktualisiert"

if [ "$MODE" = "docker" ]; then
    # ── Docker: Image neu bauen + Container neu starten ──────────
    echo "[2] Docker-Image neu bauen …"
    docker compose build
    echo "[3] Container neu starten …"
    docker compose up -d
    echo ""
    echo "=============================================="
    echo "  ✓ Update abgeschlossen (Docker)"
    echo "  Container läuft auf Port $(grep HOST_PORT .env 2>/dev/null | cut -d= -f2 || echo 8000)"
    echo "=============================================="

else
    # ── Bare-Metal: Dependencies + systemd restart ───────────────
    VENV_DIR="$APP_DIR/venv"
    if [ -d "$VENV_DIR" ]; then
        echo "[2] Dependencies aktualisieren …"
        "$VENV_DIR/bin/pip" install --quiet -r requirements.txt
        echo "    ✓ pip install fertig"
    else
        echo "[2] Kein venv gefunden – überspringe pip install"
    fi

    echo "[3] Service neu starten …"
    if systemctl is-active --quiet opman 2>/dev/null; then
        sudo systemctl restart opman
        echo "    ✓ systemd service 'opman' neugestartet"
    else
        echo "    ⚠ Service 'opman' nicht aktiv – bitte manuell starten"
    fi

    echo ""
    echo "=============================================="
    echo "  ✓ Update abgeschlossen (Bare-Metal)"
    echo "=============================================="
fi
