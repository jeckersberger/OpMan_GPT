# OpMan GPT – Installationsanleitung

## Öffentlicher Server (Internet-Betrieb, empfohlen)

### Voraussetzungen
- Ubuntu 22.04 / Debian 12 Server (x86_64 oder ARM64)
- Root-Zugriff (SSH)
- Eine Domain die auf die Server-IP zeigt (z.B. `opman.example.com`)
- Port 80 und 443 in der Firewall freigegeben

### Schnell-Installation (automatisch)

```bash
# 1. Repository klonen
git clone <repo-url> /opt/OpMan_GPT
cd /opt/OpMan_GPT

# 2. Deployment-Skript ausführen
sudo bash deploy.sh opman.example.com ubuntu
```

Das Skript erledigt alles automatisch:
- Python-Umgebung einrichten
- gunicorn als WSGI-Server starten
- nginx als Reverse Proxy konfigurieren
- Let's Encrypt HTTPS-Zertifikat holen

Die App ist danach erreichbar unter: **https://opman.example.com**

---

### Manuelle Installation (Schritt für Schritt)

#### 1. Pakete installieren
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
```

#### 2. App-Dateien ablegen
```bash
git clone <repo-url> /opt/OpMan_GPT
cd /opt/OpMan_GPT
```

#### 3. Python-Umgebung einrichten
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. App testen (optional)
```bash
# Kurz testen ob sie startet:
venv/bin/gunicorn --bind 127.0.0.1:5000 "app:create_app()"
# Mit Strg+C wieder beenden
```

#### 5. systemd-Service anlegen

Datei erstellen: `/etc/systemd/system/opman.service`
```ini
[Unit]
Description=OpMan GPT – Übungsleiter-App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/OpMan_GPT
ExecStart=/opt/OpMan_GPT/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 "app:create_app()"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Service aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable opman
sudo systemctl start opman
sudo systemctl status opman   # sollte "active (running)" zeigen
```

#### 6. nginx als Reverse Proxy konfigurieren

Datei erstellen: `/etc/nginx/sites-available/opman`
```nginx
server {
    listen 80;
    server_name opman.example.com;

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_buffering    off;
    }
}
```

Aktivieren:
```bash
sudo ln -s /etc/nginx/sites-available/opman /etc/nginx/sites-enabled/
sudo nginx -t              # Konfiguration testen
sudo systemctl reload nginx
```

#### 7. HTTPS mit Let's Encrypt einrichten
```bash
sudo certbot --nginx -d opman.example.com
```

Certbot konfiguriert nginx automatisch für HTTPS und richtet die automatische
Zertifikatserneuerung ein (läuft als systemd-Timer).

---

## Raspberry Pi (LAN-Betrieb)

Für den Betrieb im lokalen Netz (z.B. bei Übungen ohne Internet) kann der Raspi
mit selbstsigniertem Zertifikat betrieben werden.

### Voraussetzungen
- Raspberry Pi 4 mit Raspberry Pi OS (64-bit) oder Ubuntu Server
- Python 3.11+
- Alle Geräte im selben WLAN

### Installation

```bash
# 1. Repository klonen
git clone <repo-url> ~/OpMan_GPT
cd ~/OpMan_GPT

# 2. Virtualenv + Abhängigkeiten
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Selbstsigniertes Zertifikat erzeugen (einmalig)
python gen_cert.py

# 4. App starten
python run.py
```

Die App ist erreichbar unter: **https://<Raspi-IP>:5000**

Beim ersten Aufruf im Browser: Sicherheitswarnung → "Trotzdem öffnen" (wegen selbstsigniertem Zertifikat).

### Autostart auf dem Raspi (systemd)

```bash
sudo nano /etc/systemd/system/opman.service
```

```ini
[Unit]
Description=OpMan GPT – Übungsleiter-App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/OpMan_GPT
ExecStart=/home/pi/OpMan_GPT/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable opman
sudo systemctl start opman
```

---

## Verwaltung

### Service-Befehle
```bash
sudo systemctl status opman    # Status anzeigen
sudo systemctl restart opman   # Neu starten
sudo systemctl stop opman      # Stoppen
journalctl -u opman -f         # Live-Logs anzeigen
```

### App aktualisieren
```bash
cd /opt/OpMan_GPT
git pull
sudo systemctl restart opman
```

### Datenbank
Die SQLite-Datenbank liegt in `instance/opman.db` und bleibt bei Updates erhalten.
Backup:
```bash
cp instance/opman.db instance/opman_backup_$(date +%Y%m%d).db
```
