#!/bin/bash
# =============================================================================
# OpMan GPT – Deployment-Skript für Ubuntu/Debian-Server (öffentlich erreichbar)
# =============================================================================
# Verwendung:
#   sudo bash deploy.sh <domain> <user>
#
# Beispiel:
#   sudo bash deploy.sh opman.example.com ubuntu
#
# Was dieses Skript macht:
#   1. System-Pakete installieren (nginx, certbot, python3-venv)
#   2. Python-Virtualenv + Abhängigkeiten einrichten
#   3. systemd-Service anlegen (gunicorn)
#   4. nginx als Reverse Proxy konfigurieren
#   5. Let's Encrypt Zertifikat holen
# =============================================================================

set -e  # Abbruch bei Fehler

# ---------- Parameter prüfen ----------
DOMAIN="${1:-}"
APP_USER="${2:-$(logname 2>/dev/null || echo ubuntu)}"

if [ -z "$DOMAIN" ]; then
    echo "FEHLER: Domain fehlt."
    echo "Aufruf: sudo bash deploy.sh <domain> [user]"
    echo "Beispiel: sudo bash deploy.sh opman.example.com ubuntu"
    exit 1
fi

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="opman"

echo "=============================================="
echo "  OpMan GPT Deployment"
echo "  Domain:    $DOMAIN"
echo "  App-User:  $APP_USER"
echo "  App-Dir:   $APP_DIR"
echo "=============================================="

# ---------- 1. Pakete ----------
echo "[1/5] Pakete installieren..."
apt-get update -q
apt-get install -y -q python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# ---------- 2. Virtualenv + Abhängigkeiten ----------
echo "[2/5] Python-Umgebung einrichten..."
if [ ! -d "$VENV_DIR" ]; then
    sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
fi
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --quiet --upgrade pip
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# ---------- 3. systemd-Service ----------
echo "[3/5] systemd-Service einrichten..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=OpMan GPT – Übungsleiter-App
After=network.target

[Service]
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_DIR}/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 "app:create_app()"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
echo "   Service gestartet: $(systemctl is-active $SERVICE_NAME)"

# ---------- 4. nginx-Konfiguration ----------
echo "[4/5] nginx konfigurieren..."
cat > "/etc/nginx/sites-available/${SERVICE_NAME}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host \$host;
        proxy_set_header   X-Real-IP \$remote_addr;
        proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        # WebSocket-Unterstützung (SSE / Long-Polling)
        proxy_buffering    off;
    }
}
EOF

# Alte Default-Seite deaktivieren, opman aktivieren
rm -f /etc/nginx/sites-enabled/default
ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
nginx -t && systemctl reload nginx
echo "   nginx konfiguriert."

# ---------- 5. Let's Encrypt ----------
echo "[5/5] HTTPS-Zertifikat holen (Let's Encrypt)..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email
systemctl reload nginx

echo ""
echo "=============================================="
echo "  Fertig!"
echo "  Die App ist erreichbar unter:"
echo "  https://${DOMAIN}"
echo "=============================================="
