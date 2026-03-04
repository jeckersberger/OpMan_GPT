# Systemarchitektur -- OpMan_GPT

**Dokument:** Architekturdokumentation
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern

---

## 1. Systemuebersicht

OpMan_GPT ist eine webbasierte Einsatzleitsoftware (Einsatzleitstand) fuer den Sanitaetsdienst und Rettungsdienst. Das System laeuft vollstaendig lokal im LAN ohne Abhaengigkeit von Cloud-Diensten.

```
+===========================================================+
|                    OpMan_GPT System                        |
|                                                           |
|  +-------------+    +-------------+    +---------------+  |
|  |  Leitstelle |    |  EVT-App    |    |  Funkprotokoll|  |
|  |  (Browser)  |    |  (Mobil)    |    |  (Browser)    |  |
|  |  /          |    |  /evt       |    |  /protokoll   |  |
|  +------+------+    +------+------+    +-------+-------+  |
|         |                  |                   |          |
|         +--------+---------+-------------------+          |
|                  |                                        |
|         +--------v--------+                               |
|         |   Flask App     |                               |
|         |   (app.py)      |                               |
|         |                 |                               |
|         | +-------------+ |   +----------+               |
|         | | Auth (RBAC) | |   | DSGVO    |               |
|         | | auth.py     | |   | dsgvo.py |               |
|         | +-------------+ |   +----------+               |
|         | +-------------+ |   +----------+               |
|         | | Monitoring  | |   | Database |               |
|         | | monitoring. | |   | database.|               |
|         | | py          | |   | py       |               |
|         | +-------------+ |   +----------+               |
|         +--------+--------+                               |
|                  |                                        |
|         +--------v--------+                               |
|         |   SQLAlchemy    |                               |
|         |   ORM           |                               |
|         +--------+--------+                               |
|                  |                                        |
|         +--------v--------+                               |
|         | SQLite/PostgreSQL|                               |
|         | (models.py)      |                               |
|         +-----------------+                               |
+===========================================================+
```

---

## 2. Komponentendiagramm

### 2.1 Backend-Komponenten

```
+------------------------------------------------------------------+
|                        Flask Application                          |
|                                                                  |
|  +------------------+  +------------------+  +-----------------+ |
|  |     app.py       |  |    auth.py       |  |   dsgvo.py      | |
|  |                  |  |                  |  |                 | |
|  | - Einsatz-CRUD   |  | - Login/Logout   |  | - Verschluessel.| |
|  | - Trupp-CRUD     |  | - RBAC           |  | - Art.17 Loesch.| |
|  | - Disposition    |  | - Audit-Logging  |  | - Art.20 Export | |
|  | - Funkprotokoll  |  | - MFA (TOTP)     |  | - Pseudonymis.  | |
|  | - GPS-Tracking   |  | - Brute-Force    |  | - Breach-Check  | |
|  | - Web-Push       |  | - Session-Mgmt   |  | - Consent-Mgmt  | |
|  | - Falldoku       |  | - Anomalie-Det.  |  | - DSGVO-Dashb.  | |
|  | - Uebungssystem  |  | - Break-Glass    |  | - Auto-Cleanup  | |
|  +------------------+  | - Data Retention |  | - Minimierung   | |
|                         | - Access Review  |  +-----------------+ |
|  +------------------+  +------------------+                      |
|  |  monitoring.py   |  +------------------+                      |
|  |                  |  |   database.py    |                      |
|  | - /health        |  |                  |                      |
|  | - /metrics       |  | - SQLite/PgSQL   |                      |
|  | - Request-Stats  |  | - Connection Pool|                      |
|  +------------------+  | - Migrations     |                      |
|                         +------------------+                      |
+------------------------------------------------------------------+
```

### 2.2 Datenmodell

```
+------------------+     +------------------+     +------------------+
|     User         |     |     Team         |     |    Mission       |
|------------------|     |------------------|     |------------------|
| id (PK)          |     | id (PK)          |     | id (PK)          |
| username         |     | name             |     | title            |
| password_hash    |     | callsign         |     | description      |
| role             |     | color            |     | priority (1-5)   |
| display_name     |     | radio_status     |     | status           |
| mfa_secret       |     | availability     |     | lat, lng         |
| mfa_enabled      |     | radio_group      |     | archived         |
| is_active_user   |     | vehicle          |     | created_at       |
| is_locked        |     | lat, lng         |     +--------+---------+
| failed_logins    |     | created_at       |              |
| locked_until     |     +--------+---------+              |
| last_login       |              |                        |
| last_review_at   |              |                        |
+------------------+     +--------v------------------------v---------+
                         |              Assignment                    |
+------------------+     |--------------------------------------------+
|   AuditLog       |     | id (PK)                                   |
|------------------|     | team_id (FK -> Team)                      |
| id (PK)          |     | mission_id (FK -> Mission)                |
| timestamp        |     | assigned_at                               |
| user_id          |     +--------------------------------------------+
| username         |
| action           |     +------------------+     +------------------+
| resource         |     | CaseDefinition   |     |    CaseDoc       |
| resource_id      |     |------------------|     |------------------|
| details          |     | id (PK)          |     | id (PK/FK)       |
| ip_address       |     | schlagwort       |     | assigned_evt     |
| user_agent       |     | patient          |     | alarm_time       |
| hash             |     | patient_alarm    |     | status3_time     |
+------------------+     | alter            |     | status4_time     |
                         | geschlecht       |     | status7_time     |
+------------------+     | besonderheit     |     | status8_time     |
| RadioLogEntry    |     | hinweis          |     | rmi_reported     |
|------------------|     | vitals_json      |     | sk_reported      |
| id (PK)          |     | lat, lng         |     | pzc_reported     |
| team_name        |     | updated_at       |     | zielklinik       |
| callsign         |     +------------------+     | notes            |
| message          |                               +------------------+
| timestamp        |
| case_id          |     +------------------+     +------------------+
+------------------+     | PseudonymMapping |     | ConsentRecord    |
                         |------------------|     |------------------|
+------------------+     | id (PK)          |     | id (PK)          |
| UserSession      |     | original_hash    |     | data_subject     |
|------------------|     | pseudonym        |     | purpose          |
| id (PK)          |     | created_at       |     | granted_at       |
| user_id (FK)     |     +------------------+     | withdrawn_at     |
| session_id       |                               | legal_basis      |
| created_at       |     +------------------+     +------------------+
| last_seen        |     | PushSubscription |
| ip_address       |     |------------------|     +------------------+
| user_agent       |     | id (PK)          |     | BreakGlassLog    |
+------------------+     | evt_name         |     |------------------|
                         | endpoint         |     | id (PK)          |
+------------------+     | p256dh           |     | user_id (FK)     |
| ExerciseConfig   |     | auth             |     | timestamp        |
|------------------|     | created_at       |     | reason           |
| id (PK)          |     +------------------+     | approved_by      |
| evt_count        |                               | expires_at       |
| created_at       |                               +------------------+
+------------------+
```

---

## 3. Datenfluss

### 3.1 Einsatzkoordination

```
Disponent (Browser)
    |
    | 1. Einsatz anlegen (POST /api/missions)
    v
Flask App (app.py)
    |
    | 2. RBAC-Pruefung (auth.py)
    | 3. Audit-Log erstellen (auth.py)
    | 4. Datenbank-Insert (models.py)
    v
SQLite/PostgreSQL
    |
    | 5. Einsatz gespeichert
    v
Alle Clients (Polling alle 3 Sekunden)
    |
    | 6. GET /api/state -> aktueller Systemzustand
    v
Anzeige auf Lagekarte und Einsatzliste
```

### 3.2 EVT-Alarmierung

```
Disponent weist Trupp zu
    |
    | 1. POST /api/assignments
    v
Flask App
    |
    | 2. Assignment erstellt
    | 3. Web-Push ausloesen (_broadcast_push)
    v
VAPID-Server (pywebpush)
    |
    | 4. Push-Nachricht verschluesselt
    v
Browser-Push-Dienst (FCM/Mozilla)
    |
    | 5. Push an EVT-Geraet
    v
EVT-App (Service Worker)
    |
    | 6. Alarm-Overlay + Ton + Vibration
    v
EVT-Operator bestaetigt
```

### 3.3 GPS-Tracking

```
EVT-Smartphone (Browser Geolocation API)
    |
    | 1. Position alle ~10 Sek. oder bei Bewegung > 5m
    v
POST /api/teams/<id>/gps
    |
    | 2. Token-Authentifizierung (EVT-Token)
    | 3. Position in DB aktualisieren
    v
Leitstellen-Browser (Polling)
    |
    | 4. Trupp-Marker auf Karte aktualisiert
    v
Leaflet.js Karte
```

### 3.4 DSGVO-Datenfluss

```
DSGVO-Aktion (Admin/DSB)
    |
    +-- Loeschung (Art. 17)
    |     |
    |     v
    |   Patientendaten -> "GELOESCHT"
    |   Audit-Log: DSGVO_ERASURE
    |
    +-- Export (Art. 20)
    |     |
    |     v
    |   Patientendaten entschluesseln (Fernet)
    |   JSON-Export generieren
    |   Audit-Log: DSGVO_EXPORT
    |
    +-- Pseudonymisierung
    |     |
    |     v
    |   Name -> SHA-256 Hash -> Mapping-Tabelle
    |   Name -> Patient-XXXXXX
    |   Audit-Log: DSGVO_PSEUDONYMIZE
    |
    +-- Auto-Cleanup
          |
          v
        Faelle aelter als Aufbewahrungsfrist
        -> Anonymisierung
        Audit-Log: DSGVO_AUTO_CLEANUP
```

---

## 4. Schnittstellendokumentation

### 4.1 REST-API Endpunkte

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/api/state` | Gesamtzustand (Teams, Missions, Assignments) | EVT/Login |
| POST | `/api/teams` | Team erstellen | Login (disponent+) |
| PUT | `/api/teams/<id>` | Team aktualisieren | Login (disponent+) |
| DELETE | `/api/teams/<id>` | Team loeschen | Login (disponent+) |
| POST | `/api/teams/<id>/gps` | GPS-Position aktualisieren | EVT-Token |
| POST | `/api/missions` | Einsatz erstellen | Login (disponent+) |
| PUT | `/api/missions/<id>` | Einsatz aktualisieren | Login (disponent+) |
| DELETE | `/api/missions/<id>` | Einsatz loeschen | Login (disponent+) |
| POST | `/api/assignments` | Zuweisung erstellen | Login (disponent+) |
| DELETE | `/api/assignments/<id>` | Zuweisung loeschen | Login (disponent+) |
| GET/POST | `/api/radiolog` | Funkprotokoll lesen/schreiben | Login (disponent+) |
| GET | `/health` | Health-Check | Oeffentlich |
| GET | `/metrics` | Prometheus-Metriken | Oeffentlich |
| GET | `/api/audit-log` | Audit-Log abrufen | Login (admin/schichtleiter/datenschutz) |
| POST | `/api/dsgvo/auto-cleanup` | Automatische Datenbereinigung | Login (DSGVO-Rollen) |
| GET | `/api/dsgvo/export/<id>` | Einzelfall-Export | Login (DSGVO-Rollen) |
| DELETE | `/api/dsgvo/personal-data/<id>` | Personendaten anonymisieren | Login (DSGVO-Rollen) |
| POST | `/api/dsgvo/check-breach` | Breach-Pruefung | Login (DSGVO-Rollen) |

### 4.2 Web-Seiten

| Pfad | Beschreibung | Zugriffsrolle |
|------|-------------|--------------|
| `/` | Leitstellenansicht (Hauptseite) | Login |
| `/evt` | Mobile EVT-App | EVT-Token / Login |
| `/protokoll` | Funkprotokoll | Login (disponent+) |
| `/login` | Anmeldeseite | Oeffentlich |
| `/admin/users` | Benutzerverwaltung | Admin |
| `/admin/audit-log` | Audit-Log-Ansicht | Admin/Schichtleiter/DSB |
| `/dsgvo` | DSGVO-Dashboard | Admin/Schichtleiter/DSB |

---

## 5. Sicherheitsarchitektur

```
+------------------------------------------------------------------+
|                      Sicherheitsschichten                         |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Schicht 1: Netzwerk                                       |  |
|  |  - Firewall (Host-basiert)                                 |  |
|  |  - TLS/HTTPS (alle Verbindungen)                           |  |
|  |  - LAN-only Betrieb                                        |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Schicht 2: Authentifizierung                               |  |
|  |  - bcrypt Passwort-Hashing                                  |  |
|  |  - TOTP Multi-Faktor-Authentifizierung                      |  |
|  |  - Account-Sperrung (Brute-Force-Schutz)                    |  |
|  |  - Session-Limiting (1 Session/Benutzer)                    |  |
|  |  - EVT-Token (QR-Code-basiert)                              |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Schicht 3: Autorisierung                                   |  |
|  |  - RBAC (7 Rollen, hierarchisch)                            |  |
|  |  - CSRF-Schutz (Flask-WTF)                                  |  |
|  |  - Rate Limiting (Flask-Limiter)                             |  |
|  |  - Break-Glass (Notfallzugriff)                              |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Schicht 4: Datenschutz                                     |  |
|  |  - Fernet-Verschluesselung (Patientennamen)                 |  |
|  |  - Pseudonymisierung                                        |  |
|  |  - Einwilligungsverwaltung                                  |  |
|  |  - Automatische Anonymisierung                              |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Schicht 5: Audit und Erkennung                             |  |
|  |  - Hash-Chain Audit-Log (SHA-256)                           |  |
|  |  - Anomalie-Erkennung                                      |  |
|  |  - Breach-Indikator-Pruefung                                |  |
|  |  - API-Zugriffs-Logging                                     |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## 6. Deployment-Architektur

### 6.1 Standalone (Empfohlen fuer Uebungen)

```
+----------------------------------+
|         Server (Linux)           |
|                                  |
|  Gunicorn (WSGI)                |
|    |                            |
|    +-- Flask App (OpMan_GPT)    |
|    |     |                      |
|    |     +-- SQLite DB          |
|    |                            |
|  Nginx (optional, Reverse Proxy)|
+----------------------------------+
         |
    LAN (Ethernet/WLAN)
         |
+--------+--------+
|                  |
Browser         EVT-App
(Leitstelle)    (Smartphone)
```

### 6.2 Docker

```
+----------------------------------+
|     docker-compose               |
|                                  |
|  +----------------------------+  |
|  | opman-app Container       |  |
|  |                            |  |
|  | Gunicorn + Flask + SQLite  |  |
|  | Port: 5000, 5443          |  |
|  | Volume: ./instance         |  |
|  +----------------------------+  |
+----------------------------------+
```

### 6.3 Produktion (mit PostgreSQL)

```
+----------------------------------+
|         Application Server       |
|                                  |
|  Nginx (Reverse Proxy, TLS)     |
|    |                            |
|  Gunicorn (4 Workers)           |
|    |                            |
|  Flask App (OpMan_GPT)          |
+----------------------------------+
         |
    Netzwerk (verschluesselt)
         |
+----------------------------------+
|         Database Server          |
|                                  |
|  PostgreSQL                      |
|  SSL: require                   |
|  Pool: 10 + 20 overflow         |
+----------------------------------+
```

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
