# Runbook -- Betriebshandbuch OpMan_GPT

**Dokument:** Operations Runbook
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern

---

## 1. Systemuebersicht

| Komponente | Technologie | Pfad / Port |
|-----------|------------|-------------|
| Anwendung | Python 3 / Flask 3 | /home/user/OpMan_GPT/ |
| WSGI-Server | Gunicorn | Port 5000 (HTTP), 5443 (HTTPS) |
| Datenbank | SQLite (Standard) / PostgreSQL | instance/einsatzleiter.db |
| Konfiguration | Umgebungsvariablen + app.py | .env / docker-compose.yml |
| Zertifikate | Selbstsigniert (gen_cert.py) | instance/cert.pem, instance/key.pem |
| Verschluesselungsschluessel | Fernet (AES-128) | instance/encryption.key |
| VAPID-Schluessel | Web-Push | instance/vapid_keys.json |
| EVT-Token | QR-Code-Zugang | instance/evt_token.txt |

---

## 2. Start- und Stop-Verfahren

### 2.1 Anwendung starten

**Entwicklung (direkt):**
```bash
cd /home/user/OpMan_GPT
python app.py
# Laeuft auf http://0.0.0.0:5000
```

**Produktion (Gunicorn):**
```bash
cd /home/user/OpMan_GPT
gunicorn -c gunicorn.conf.py run:app
```

**Docker:**
```bash
cd /home/user/OpMan_GPT
docker-compose up -d
```

### 2.2 Anwendung stoppen

**Gunicorn (graceful):**
```bash
# PID ermitteln
cat /tmp/gunicorn.pid
# Oder:
pgrep -f gunicorn

# Graceful Stop (wartet auf laufende Requests)
kill -SIGTERM $(cat /tmp/gunicorn.pid)

# Bei Problemen: Force Stop
kill -SIGKILL $(cat /tmp/gunicorn.pid)
```

**Docker:**
```bash
docker-compose down
```

### 2.3 Anwendung neustarten

```bash
# Gunicorn Graceful Restart (Zero-Downtime)
kill -SIGHUP $(cat /tmp/gunicorn.pid)

# Docker
docker-compose restart
```

### 2.4 Startpruefung nach Neustart

- [ ] Health-Check: `curl http://localhost:5000/health`
- [ ] Login-Seite erreichbar: `curl -I http://localhost:5000/login`
- [ ] Datenbank-Verbindung: Health-Check zeigt `database: healthy`
- [ ] Metriken verfuegbar: `curl http://localhost:5000/metrics`
- [ ] HTTPS funktioniert (falls konfiguriert): `curl -k https://localhost:5443/health`

---

## 3. Haeufige Fehlersuche (Troubleshooting)

### 3.1 Anwendung startet nicht

| Symptom | Moegliche Ursache | Loesung |
|---------|-------------------|---------|
| `ModuleNotFoundError` | Fehlende Abhaengigkeit | `pip install -r requirements.txt` |
| `Address already in use` | Port bereits belegt | `lsof -i :5000` und Prozess beenden |
| `PermissionError: encryption.key` | Dateiberechtigungen | `chmod 600 instance/encryption.key` |
| `sqlite3.OperationalError: database is locked` | Paralleler Zugriff | Gunicorn mit preload_app=True |
| `ImportError: bcrypt` | bcrypt nicht installiert | `pip install bcrypt>=4.0` |

### 3.2 Datenbank-Probleme

| Symptom | Loesung |
|---------|---------|
| `database is locked` | Alle DB-Verbindungen schliessen, Anwendung neustarten |
| `database disk image is malformed` | Aus Backup wiederherstellen; `sqlite3 db.db ".recover"` |
| Langsame Abfragen | `sqlite3 db.db "ANALYZE; VACUUM;"` |
| Tabelle fehlt | Anwendung neu starten (db.create_all wird aufgerufen) |
| Migration fehlgeschlagen | Log pruefen, manuelle Migration ausfuehren |

### 3.3 Authentifizierungs-Probleme

| Symptom | Loesung |
|---------|---------|
| Admin-Account gesperrt | `sqlite3 instance/einsatzleiter.db "UPDATE users SET is_locked=0, failed_logins=0, locked_until=NULL WHERE username='admin';"` |
| Admin-Passwort vergessen | Neues Passwort-Hash generieren: `python -c "import bcrypt; print(bcrypt.hashpw(b'neuespasswort', bcrypt.gensalt()).decode())"` und in DB aktualisieren |
| MFA-Token ungueltig | Zeitabweichung pruefen (`ntpdate` ausfuehren); MFA zuruecksetzen |
| Session-Probleme | Browser-Cookies loeschen; `SECRET_KEY` pruefen |
| CSRF-Fehler | CSRF-Token im Formular pruefen; Cache leeren |

### 3.4 Netzwerk-Probleme

| Symptom | Loesung |
|---------|---------|
| HTTPS-Zertifikat ungueltig | `python gen_cert.py` fuer neues Zertifikat |
| Push-Benachrichtigungen kommen nicht | VAPID-Keys pruefen; HTTPS erforderlich |
| GPS funktioniert nicht auf mobilen Geraeten | HTTPS erforderlich; Standortberechtigung pruefen |
| EVT-App laed nicht | EVT-Token pruefen; QR-Code neu generieren |
| Karten werden nicht angezeigt | Internetverbindung fuer OSM-Kacheln pruefen |

---

## 4. Backup und Restore

### 4.1 Manuelles Backup erstellen

```bash
# Datenbank sichern
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p /home/user/OpMan_GPT/backup
cp /home/user/OpMan_GPT/instance/einsatzleiter.db \
   /home/user/OpMan_GPT/backup/db_${DATE}.db
gzip /home/user/OpMan_GPT/backup/db_${DATE}.db

# Schluessel sichern (separat aufbewahren!)
cp /home/user/OpMan_GPT/instance/encryption.key \
   /home/user/OpMan_GPT/backup/encryption_${DATE}.key

# VAPID-Keys sichern
cp /home/user/OpMan_GPT/instance/vapid_keys.json \
   /home/user/OpMan_GPT/backup/vapid_${DATE}.json

echo "Backup erstellt: ${DATE}"
```

### 4.2 Restore aus Backup

```bash
# 1. Anwendung stoppen
kill -SIGTERM $(cat /tmp/gunicorn.pid 2>/dev/null) 2>/dev/null

# 2. Aktuelle DB sichern (falls moeglich)
cp instance/einsatzleiter.db instance/einsatzleiter.db.before_restore

# 3. Backup entpacken und einspielen
gunzip backup/db_YYYYMMDD_HHMMSS.db.gz
cp backup/db_YYYYMMDD_HHMMSS.db instance/einsatzleiter.db

# 4. Verschluesselungsschluessel pruefen/wiederherstellen
# WICHTIG: Schluessel muss zum Backup passen!
# cp backup/encryption_YYYYMMDD_HHMMSS.key instance/encryption.key

# 5. Berechtigungen setzen
chmod 600 instance/encryption.key
chmod 644 instance/einsatzleiter.db

# 6. Anwendung starten
gunicorn -c gunicorn.conf.py run:app

# 7. Health-Check
curl http://localhost:5000/health
```

### 4.3 Automatisches Backup (Cronjob)

```bash
# Crontab-Eintrag (taeglich um 02:00 Uhr)
0 2 * * * /home/user/OpMan_GPT/scripts/backup.sh >> /var/log/opman_backup.log 2>&1
```

---

## 5. Benutzerverwaltung

### 5.1 Benutzer anlegen

**Ueber Web-UI:**
1. Als Admin anmelden
2. `/admin/users` aufrufen
3. Benutzername, Passwort (min. 8 Zeichen), Rolle eingeben
4. "Erstellen" klicken

**Ueber Kommandozeile:**
```python
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User(username="neuer_benutzer", role="disponent")
    user.set_password("sicheres_passwort")
    db.session.add(user)
    db.session.commit()
    print(f"Benutzer '{user.username}' erstellt")
```

### 5.2 Passwort zuruecksetzen

**Ueber Web-UI:**
1. Als Admin anmelden -> `/admin/users`
2. Neues Passwort eingeben -> "PW Reset" klicken

**Ueber Datenbank (Notfall):**
```bash
# bcrypt-Hash generieren
HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'neues_passwort', bcrypt.gensalt()).decode())")

# In DB aktualisieren
sqlite3 instance/einsatzleiter.db \
  "UPDATE users SET password_hash='${HASH}', is_locked=0, failed_logins=0 WHERE username='admin';"
```

### 5.3 Benutzer sperren/entsperren

**Ueber Web-UI:** `/admin/users` -> "Sperren"/"Entsperren"

**Ueber Datenbank:**
```bash
# Sperren
sqlite3 instance/einsatzleiter.db \
  "UPDATE users SET is_locked=1 WHERE username='benutzername';"

# Entsperren
sqlite3 instance/einsatzleiter.db \
  "UPDATE users SET is_locked=0, failed_logins=0, locked_until=NULL WHERE username='benutzername';"
```

### 5.4 MFA zuruecksetzen

```bash
sqlite3 instance/einsatzleiter.db \
  "UPDATE users SET mfa_secret=NULL, mfa_enabled=0 WHERE username='benutzername';"
```

---

## 6. Monitoring-Alerts und Reaktionen

### 6.1 Health-Check Endpunkt

**URL:** `GET /health`

| Status | Bedeutung | Aktion |
|--------|----------|--------|
| `healthy` (HTTP 200) | Alles in Ordnung | Keine |
| `degraded` (HTTP 200) | Eingeschraenkt, aber funktionsfaehig | Pruefen und beheben |
| `unhealthy` (HTTP 503) | Kritischer Ausfall | Sofort reagieren |

**Ueberwachte Komponenten:**
- Datenbank-Verbindung
- Festplattenspeicher (Warnung > 90%, Kritisch > 95%)
- Arbeitsspeicher (Warnung > 90%, Kritisch > 95%)

### 6.2 Prometheus-Metriken

**URL:** `GET /metrics`

| Metrik | Beschreibung | Alarm-Schwelle |
|--------|-------------|---------------|
| `opman_requests_total` | Gesamtzahl Requests | Trend-Ueberwachung |
| `opman_errors_total` | 5xx-Fehler | > 10 / 5 Min |
| `opman_active_requests` | Aktive Requests | > 50 |
| `opman_request_latency_seconds_sum` | Gesamt-Latenz | Durchschnitt > 1s |
| `opman_active_users` | Aktive Benutzerkonten | Unerwartete Aenderung |

### 6.3 Alert-Reaktionen

| Alert | Reaktion |
|-------|---------|
| Health: unhealthy (Database) | DB-Verbindung pruefen, ggf. Neustart |
| Health: unhealthy (Disk > 95%) | Festplatte bereinigen, Logs rotieren, alte Backups loeschen |
| Health: unhealthy (Memory > 95%) | Prozesse pruefen, ggf. Neustart |
| Errors > 10/5min | Error-Logs pruefen: `journalctl -u opman -n 100` |
| Active Requests > 50 | DDoS/Missbrauch pruefen, Rate Limiting pruefen |
| Latency > 1s | DB-Performance pruefen, VACUUM ausfuehren |

---

## 7. Log-Dateien

| Log | Pfad | Rotation |
|-----|------|---------|
| Gunicorn Access | stdout / journald | Taeglich |
| Gunicorn Error | stderr / journald | Taeglich |
| Audit-Log | Datenbank (audit_log Tabelle) | Per Data Retention API |
| System-Log | /var/log/syslog | Automatisch (logrotate) |

**Audit-Log abfragen:**
```bash
# Letzte 20 Eintraege
sqlite3 instance/einsatzleiter.db \
  "SELECT datetime(timestamp), username, action, details FROM audit_log ORDER BY id DESC LIMIT 20;"

# Fehlgeschlagene Logins
sqlite3 instance/einsatzleiter.db \
  "SELECT datetime(timestamp), username, ip_address FROM audit_log WHERE action='LOGIN_FAILED' ORDER BY id DESC LIMIT 20;"
```

---

## 8. Wartungsarbeiten

### 8.1 Regelmaessige Wartung

| Aufgabe | Turnus | Befehl / Vorgehen |
|---------|--------|-------------------|
| Datenbank optimieren | Woechtentlich | `sqlite3 instance/einsatzleiter.db "VACUUM; ANALYZE;"` |
| Abhaengigkeiten aktualisieren | Monatlich | `pip install --upgrade -r requirements.txt` |
| Sicherheitsupdates OS | Woechtentlich | `apt update && apt upgrade` |
| SSL-Zertifikat erneuern | Vor Ablauf | `python gen_cert.py` |
| Log-Rotation pruefen | Monatlich | Festplattenplatz pruefen |
| Backup-Test | Monatlich | Restore auf Testumgebung |
| Access Review | Alle 90 Tage | `curl /api/admin/access-review` |
| DSGVO Auto-Cleanup | Woechtentlich | `curl -X POST /api/dsgvo/auto-cleanup` |

### 8.2 Wartungsfenster

- **Geplante Wartung:** Samstag 02:00 - 04:00 Uhr (nach Absprache mit Leitstellenleitung)
- **Ankuendigung:** Mindestens 48 Stunden vorher
- **Notbetrieb:** Waehrend der Wartung Papierverfahren bereithalten

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
