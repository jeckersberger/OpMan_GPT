# Security-Audit – OpMan-GPT

**Datum:** 2026-03-15
**Projekt:** OpMan-GPT – Übungsmanagementsystem für BRK Funkübungen
**Auditor:** Coding Assistant (automatisiertes Review)

---

## 1. Projektübersicht

**Was wurde gebaut?**
Eine Flask-basierte Einsatzleiter-Web-App für Sanitätsübungen des BRK Feucht. Das System koordiniert EVT-Teams (Einsatzvorsorge-Trupps) mit GPS-Tracking, Funkprotokoll, Patientendokumentation und mobiler EVT-App.

**Technologien:**
- Backend: Python 3, Flask 3.0.3, SQLAlchemy (SQLite)
- Frontend: Vanilla JavaScript, Leaflet.js (Karten), HTML/CSS
- Deployment: Docker, gunicorn, nginx, Let's Encrypt
- Zusätzlich: Web-Push (VAPID/pywebpush), what3words API, QR-Code-Generierung

**Welche Daten verarbeitet das Programm?**
- GPS-Standorte der EVT-Teams (personenbeziehbar)
- Teambezeichnungen und Rufnamen
- Funkprotokoll-Einträge (Übungskommunikation)
- Fiktive Patientendaten (Übungsfälle mit Namen, Alter, Geschlecht, Diagnosen)
- Web-Push-Abonnements (Endpoint-URLs, Schlüssel)
- VAPID-Schlüssel, W3W API-Key, GitHub-Zugangsdaten

---

## 2. Sicherheitsmaßnahmen im Detail

### 2.1 SQL-Injection-Schutz ✅
- **Was:** Durchgängige Nutzung von SQLAlchemy ORM mit parametrisierten Abfragen
- **Warum:** Verhindert, dass über Eingabefelder Datenbankbefehle eingeschleust werden
- **Wo:** Alle DB-Zugriffe in `app.py` und `models.py`
- **Standard:** OWASP Top 10 – A03:2021 Injection

### 2.2 HTTPS/TLS ✅
- **Was:** Automatische Zertifikatsgenerierung (self-signed) für lokalen Betrieb; Let's Encrypt für Produktiv
- **Warum:** Verschlüsselt die Kommunikation, erforderlich für GPS auf mobilen Geräten
- **Wo:** `run.py`, `deploy.sh`
- **Standard:** Best Practice Transport Layer Security

### 2.3 HTML-Escaping (teilweise) ⚠️
- **Was:** `esc()`-Hilfsfunktion in den JavaScript-Templates escaped `&`, `<`, `>`, `"`, `'`
- **Warum:** Verhindert XSS (Cross-Site Scripting)
- **Wo:** `static/app.js`, `templates/beobachter.html`, `templates/protokoll.html`, `templates/evt.html`
- **Einschränkung:** Inkonsequent angewendet – nicht alle dynamischen Werte werden escaped

### 2.4 SQLite WAL-Modus ✅
- **Was:** WAL (Write-Ahead Logging) + busy_timeout für gleichzeitige Zugriffe
- **Warum:** Verhindert Datenbank-Locks bei mehreren gunicorn-Workern
- **Wo:** `app.py:194-199`

### 2.5 Docker Security ✅
- **Was:** `no-new-privileges: true` im Docker-Container
- **Warum:** Verhindert Privilege Escalation im Container
- **Wo:** `docker-compose.yml`

---

## 3. OWASP Top 10 Abdeckung (2021)

### A01:2021 – Broken Access Control ❌ OFFEN
**Bewertung:** Keine Authentifizierung oder Autorisierung vorhanden. Alle API-Endpoints sind offen zugänglich. Jeder im Netzwerk kann:
- Übungsdaten löschen (`POST /api/reset`)
- App-Updates auslösen (`POST /api/update`)
- Teams erstellen/löschen
- Patientendaten einsehen

**Empfehlung:** Mindestens ein einfacher Passwortschutz (z.B. HTTP Basic Auth oder Session-basierter Login) für administrative Funktionen (Reset, Update, Team-Verwaltung). Die EVT-App kann ggf. ohne Auth bleiben.

### A02:2021 – Cryptographic Failures ⚠️ TEILWEISE
**Bewertung:**
- ✅ HTTPS/TLS verfügbar
- ❌ `SECRET_KEY` hat einen bekannten Fallback-Wert (`"dev-only-change-in-production"` in `app.py:179`)
- ❌ W3W API-Key hardcoded als Fallback (`app.py:112`)
- ❌ VAPID-Keys (`vapid_keys.json`) im Repository eingecheckt

**Empfehlung:** SECRET_KEY ohne Fallback konfigurieren (Fehler werfen wenn nicht gesetzt). API-Key nur aus Umgebungsvariable lesen. VAPID-Keys aus dem Repo entfernen.

### A03:2021 – Injection ⚠️ TEILWEISE
**Bewertung:**
- ✅ SQL-Injection: Vollständig geschützt durch SQLAlchemy ORM
- ❌ XSS: Über 40 Stellen mit `innerHTML` in den Templates, teilweise ohne Escaping
- ❌ Template Injection: `{{ initial_data | safe }}` in `index.html:250` erlaubt JavaScript-Injection über Datenbank-Inhalte
- ❌ Command Injection: `entrypoint.sh` baut Git-URLs mit Token-Variablen via String-Interpolation

**Empfehlung:** `| safe` durch `| tojson` ersetzen. Konsequente Nutzung der `esc()`-Funktion oder Migration zu `textContent`.

### A04:2021 – Insecure Design ⚠️ TEILWEISE
**Bewertung:**
- ❌ Keine CSRF-Protection (kein Flask-WTF, keine Token)
- ❌ Kein Rate Limiting auf API-Endpoints
- ✅ Saubere Datentrennung (Models/Routes/Serialization)
- ✅ Graceful Restart-Mechanismus

**Empfehlung:** Flask-WTF für CSRF-Schutz einsetzen. Rate Limiting für Reset- und Update-Endpoints.

### A05:2021 – Security Misconfiguration ⚠️ TEILWEISE
**Bewertung:**
- ✅ Debug-Modus deaktiviert in Produktion (`debug=False`)
- ❌ Fehlende Security-Headers in nginx (CSP, X-Frame-Options, HSTS, X-Content-Type-Options)
- ❌ SECRET_KEY Fallback ermöglicht Session-Fälschung

**Empfehlung:** Security-Headers in nginx/deploy.sh konfigurieren.

### A06:2021 – Vulnerable and Outdated Components ⚠️ TEILWEISE
**Bewertung:**
- ✅ Aktuelle Flask-Version (3.0.3)
- ⚠️ Keine Version-Pins für `pywebpush`, `qrcode`, `cryptography` (nur Mindestversionen)
- ⚠️ Keine automatische Dependency-Prüfung (kein `pip audit` oder Dependabot)

**Empfehlung:** Exakte Versions-Pins in `requirements.txt`. CI/CD mit `pip audit`.

### A07:2021 – Identification and Authentication Failures ❌ OFFEN
**Bewertung:** Keine Authentifizierung vorhanden. Das System vertraut darauf, dass es nur im LAN erreichbar ist.

**Empfehlung:** Mindestens Basic Auth oder Session-Login für Einsatzleiter-Funktionen.

### A08:2021 – Software and Data Integrity Failures ⚠️ TEILWEISE
**Bewertung:**
- ❌ `/api/update` führt `git pull` + `pip install` ohne Integritätsprüfung aus
- ❌ Kein Content-Security-Policy Header
- ✅ Import-Funktion für Cases validiert JSON-Struktur

**Empfehlung:** Hash-Verifizierung für Updates. CSP-Header setzen.

### A09:2021 – Security Logging and Monitoring Failures ❌ OFFEN
**Bewertung:** Kein Security-Logging. Fehlgeschlagene Zugriffe, ungewöhnliche Aktivitäten und Fehler werden nicht protokolliert. Viele `except: pass`-Blöcke verschlucken Fehler still.

**Empfehlung:** Structured Logging mit Python `logging`-Modul. Fehler in `except`-Blöcken loggen statt ignorieren.

### A10:2021 – Server-Side Request Forgery (SSRF) ⚠️ TEILWEISE
**Bewertung:**
- ⚠️ W3W-API-Auflösung (`resolve_w3w`) macht HTTP-Requests an externe URLs. Die URL wird aus der Datenbank konstruiert und nicht gegen SSRF gehärtet.
- Das Risiko ist gering, da nur `api.what3words.com` angesprochen wird und die Eingabe auf das w3w-Format beschränkt ist.

**Empfehlung:** URL-Whitelist für externe API-Calls.

---

## 4. DSGVO-Compliance

### Welche personenbezogenen Daten werden verarbeitet?
| Datum | Kategorie | Speicherort |
|-------|-----------|-------------|
| GPS-Standorte | Standortdaten (Art. 9 potenziell) | SQLite DB (teams.lat/lng) |
| Teambezeichnungen | Pseudonym | SQLite DB |
| Funkprotokoll | Kommunikationsdaten | SQLite DB |
| Web-Push-Endpoints | Geräte-Identifier | SQLite DB |
| Fiktive Patientennamen | Übungsdaten (kein Personenbezug) | SQLite DB + Code |

### Datensparsamkeit ✅
- GPS nur bei aktiver Zustimmung (Browser-Geolocation-API)
- Push nur bei aktiver Aktivierung
- Keine Klarnamen der Teilnehmer erforderlich (nur EVT-Bezeichnungen)

### Zweckbindung ✅
- Daten werden ausschließlich für die Übungsdurchführung verwendet
- Keine Weitergabe an Dritte

### Transparenz ✅
- Datenschutzerklärung vorhanden (`/datenschutz`)
- Erklärt GPS-Nutzung, Speicherung, Löschung, Rechte

### Löschbarkeit ✅
- Reset-Funktion löscht alle Übungsdaten (`POST /api/reset`)
- Push-Abonnements können gelöscht werden

### Technische Maßnahmen ⚠️
- ✅ Lokale Speicherung (kein Cloud-Upload)
- ✅ HTTPS/TLS-Verschlüsselung
- ❌ Kein Zugriffsschutz (jeder im Netz kann Daten einsehen)
- ❌ Keine Verschlüsselung der Datenbank

### DSGVO-Lücken
1. **Datenschutzerklärung unvollständig:** Fehlende Angabe der Speicherdauer ("bis zum Reset" ist unklar), kein Hinweis auf Datenschutzbeauftragten des BRK KV
2. **GPS-Daten in DB:** Entgegen der Datenschutzerklärung (die sagt "nur im Arbeitsspeicher") werden GPS-Koordinaten in der SQLite-Datenbank persistiert (`teams.lat`, `teams.lng`, `teams.gps_updated_at`)
3. **W3W-API:** Standortdaten werden an what3words.com übertragen (externer Dienst) – in der Datenschutzerklärung steht "keine Übertragung an externe Server"
4. **Keine automatische Löschung:** Daten bleiben bestehen bis manuell ein Reset ausgeführt wird

**Empfehlung:** Datenschutzerklärung korrigieren (GPS-Persistenz und W3W-API-Nutzung erwähnen). Automatische Datenlöschung nach Übungsende implementieren.

---

## 5. Barrierefreiheit (WCAG 2.1)

### Umgesetzte Maßnahmen
- ✅ Responsive Design (Meta-Viewport, mobile Layouts)
- ✅ Gute Farbkontraste im dunklen Theme

### Fehlende Maßnahmen
- ❌ Keine ARIA-Labels auf interaktiven Elementen
- ❌ Keine `<label>`-Elemente für Formularfelder (Cases-Editor)
- ❌ Tastaturnavigation nicht durchgängig getestet
- ❌ Kein Skip-Navigation-Link
- ❌ Farbcodierung (Funkstatus) ohne textliche Alternative in manchen Views

**Erreichtes Level:** Teilweise Level A
**Empfehlung:** ARIA-Labels für Buttons/Icons ergänzen, Labels für Formularfelder, Tastaturnavigation testen.

---

## 6. Eingabevalidierung & Edge Cases

### Stellen mit Nutzereingaben
| Eingabe | Validierung | Risiko |
|---------|-------------|--------|
| Team-Name | `.strip()`, Fallback auf Auto-Name | Gering |
| Funkstatus | Prüfung gegen `RADIO_STATUS_LABELS` | ✅ OK |
| Availability | Prüfung gegen `ALLOWED_AVAILABILITY` | ✅ OK |
| Case-ID | `.strip().upper()` | Gering |
| Radiolog sender/message | `.strip()`, Pflichtfeld-Check | ✅ OK |
| EVT-Count | `int()` + Range-Check 1-6 | ✅ OK |
| Base-URL | `.strip().rstrip("/")` | ⚠️ Keine URL-Validierung |
| CaseDefinition Felder | `.strip()` diverse | ⚠️ Keine Längenprüfung |
| JSON-Import | Typ-Check `isinstance(list)` | ⚠️ Minimale Validierung |

### Abgesicherte Edge Cases
- Doppelte Zuweisungen (Team → Mission): Prüfung auf `existing`
- EVT-Wechsel: Snapshot-Sicherung der Auswertungsdaten
- Fehlende Koordinaten: Fallback auf Cache/None
- Keine Internet-Verbindung: Proxy-Fallback bei W3W

### Offene Edge Cases
- `int()` ohne try/except bei radio_status und priority
- Keine Längenbeschränkung bei Freitext-Feldern (notes, message)
- Kein Check ob Team-Name unique ist

---

## 7. Bekannte Einschränkungen & Empfehlungen

### Was das Programm NICHT absichern kann
1. **LAN-Sicherheit:** Das System vertraut auf die Netzwerk-Sicherheit. Jeder im LAN hat vollen Zugriff.
2. **Datenbank-Verschlüsselung:** SQLite speichert Daten unverschlüsselt auf der Festplatte.
3. **Backup:** Keine automatische Datensicherung der Übungsdaten.

### Empfehlungen vor Produktiveinsatz
1. **Authentifizierung einbauen** – Mindestens HTTP Basic Auth für Einsatzleiter-Funktionen
2. **CSRF-Schutz** – Flask-WTF integrieren
3. **`| safe` → `| tojson`** – XSS in index.html beheben
4. **SECRET_KEY** – Fallback entfernen, Pflicht-Konfiguration erzwingen
5. **W3W API-Key** – Aus dem Quellcode entfernen, nur über `.env`
6. **Security-Headers** – CSP, X-Frame-Options, HSTS in nginx
7. **Datenschutzerklärung** – GPS-Persistenz und W3W-API-Nutzung korrekt dokumentieren
8. **Logging** – Structured Logging für Fehler und Security-Events
9. **Dependency-Audit** – `pip audit` in CI/CD integrieren

---

## 8. Zusammenfassung

### Gesamtbewertung

**Für den vorgesehenen Einsatzzweck** (BRK-interne Funkübungen im geschützten LAN) ist OpMan-GPT **gut einsetzbar**. Die Kernfunktionalität ist solide gebaut, SQL-Injection ist vollständig verhindert, und die Datenarchitektur ist sauber.

**Größte verbleibende Risiken:**
1. 🔴 Keine Authentifizierung – jeder im Netz kann alles
2. 🔴 XSS via `| safe` Filter und innerHTML
3. 🔴 Hardcoded API-Key und SECRET_KEY-Fallback
4. 🟡 DSGVO-Inkonsistenzen (Datenschutzerklärung vs. tatsächliches Verhalten)
5. 🟡 Fehlende CSRF-Protection

**Empfohlene Priorisierung:**
1. `| safe` → `| tojson` (5 Minuten Fix, behebt kritische XSS)
2. SECRET_KEY-Fallback entfernen (2 Minuten Fix)
3. W3W API-Key aus Code entfernen (2 Minuten Fix)
4. Datenschutzerklärung korrigieren (30 Minuten)
5. Authentifizierung für Admin-Endpoints (größerer Umbau)

**Fazit:** Für geschlossene LAN-Übungen mit vertrauenswürdigen Teilnehmern akzeptables Risiko. Für öffentlich erreichbare Installationen oder Übungen mit externen Teilnehmern sind die Punkte 1-5 zwingend erforderlich.
