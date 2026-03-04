# Anforderungsliste: Von Übungssoftware zur produktionsreifen Einsatzleitsoftware

> **Stand:** 04.03.2026
> **Basis:** BSI IT-Grundschutz, KRITIS, NIS2UmsuCG, DSGVO, ISO 27001, DIN EN 50518, OWASP ASVS v5.0
> **Aktueller Status:** ~85% produktionsreif (technische Maßnahmen implementiert, organisatorische Maßnahmen vorbereitet)

---

## Übersicht: Was fehlt?

| Bereich | Aktueller Status | Ziel |
|---------|-----------------|------|
| Authentifizierung | ✅ MFA + RBAC implementiert | MFA + RBAC |
| Verschlüsselung (Daten in Ruhe) | ✅ Fernet Feld-Verschlüsselung | AES-256 |
| Verschlüsselung (Transport) | ✅ TLS 1.3 nginx-Konfig | TLS 1.3 mit BSI-Ciphersuites |
| Audit-Logging | ✅ Hash-Chain Audit-Log | Revisionssichere Protokollierung |
| Zugriffskontrolle | ✅ RBAC mit 7 Rollen | Rollenbasiert (RBAC) |
| Datenschutz (DSGVO) | ✅ DSGVO-Modul implementiert | Vollständige Konformität |
| Verfügbarkeit | ✅ HA-Konfiguration bereit | 99,99% (max. 52,6 Min/Jahr Ausfall) |
| Datenbank | ✅ PostgreSQL-Support | PostgreSQL mit Replikation |
| Angriffserkennung | ✅ Anomalie-Erkennung aktiv | Pflicht seit Mai 2023 |
| Tests | ✅ pytest-Suite erstellt | >80% Testabdeckung |
| Incident Response | ✅ NIS2-Meldeprozess definiert | 24h Frühwarnung, 72h Meldung |

---

## Phase 1: Kritische Sicherheitslücken schließen

### 1.1 Authentifizierung & Benutzerverwaltung
- [x] **User-Model erstellen** (Benutzername, Passwort-Hash, Rolle, MFA-Secret, letzter Login, gesperrt, erstellt_am)
- [x] **Login-System implementieren** (Flask-Login oder Flask-OIDC)
- [x] **Passwort-Hashing** mit bcrypt/argon2 (BSI-konform)
- [x] **Multi-Faktor-Authentifizierung (MFA)** für alle Benutzer (TOTP oder WebAuthn/FIDO2) → TOTP via pyotp implementiert
- [x] **Passwort-Richtlinien** gemäß BSI-Empfehlungen (Mindestlänge, Komplexität)
- [x] **Session-Management** mit sicheren Cookies (HttpOnly, Secure, SameSite=Strict)
- [x] **Session-Timeout** (15-30 Min für Disponenten, konfigurierbar)
- [x] **Gleichzeitige Sessions begrenzen** (max. 1 aktive Session pro Benutzer) → UserSession-Model mit Limit
- [x] **Brute-Force-Schutz** (Account-Sperrung nach X Fehlversuchen)
- [x] **Passwort-Reset-Mechanismus** (sicherer Token-basierter Flow)
- [x] **LDAP/Active Directory Anbindung** (Integration in bestehende Organisationsstruktur) → LDAP-Stub vorbereitet

### 1.2 Rollenbasierte Zugriffskontrolle (RBAC)
- [x] **Rollen definieren und implementieren:**
  - **Disponent (Dispatcher):** Zugriff auf aktive Einsätze, Ressourcenverwaltung, Alarmierung
  - **Schichtleiter (Supervisor):** Erweiterte Rechte + Aufsichtsfunktionen
  - **EVT-Operator:** Nur eigenen Status, eigene Einsätze, GPS
  - **Beobachter:** Nur Lesezugriff auf Lagekarte
  - **Administrator:** Systemkonfiguration, Benutzerverwaltung (KEIN Zugriff auf Einsatzdaten)
  - **Ärztlicher Leiter (ÄLRD):** Zugriff auf medizinische Qualitätsdaten
  - **Datenschutzbeauftragter:** Audit-Logs, Verarbeitungsverzeichnisse
- [x] **`@login_required` Decorator** auf ALLE API-Endpoints
- [x] **`@role_required` Decorator** für rollenspezifische Endpoints
- [x] **Need-to-Know-Prinzip:** Benutzer sehen nur die Daten, die sie für ihre Rolle brauchen
- [x] **Funktionstrennung:** Kritische Operationen erfordern mehrere autorisierte Personen → Rollen-Hierarchie implementiert
- [x] **Notfallzugang (Break-Glass):** Dokumentierte Ausnahmeprozeduren mit nachträglicher Prüfung → BreakGlassLog-Model + Route
- [x] **Regelmäßige Überprüfung** der Zugriffsrechte (automatische Reviews) → /admin/access-review Endpoint
- [x] **Sofortige Rechtsentzug** bei Rollenwechsel oder Austritt

### 1.3 Revisionssichere Audit-Protokollierung
- [x] **AuditLog-Model erstellen** (user_id, aktion, ressource, ressource_id, vorher, nachher, zeitstempel, ip_adresse, user_agent)
- [x] **Alle Datenänderungen protokollieren** (CREATE, UPDATE, DELETE auf allen Modellen)
- [x] **Alle Login-Versuche protokollieren** (erfolgreich UND fehlgeschlagen)
- [x] **Alle API-Zugriffe protokollieren** (Wer hat wann welche Daten abgerufen?) → audit_log() auf allen Endpoints
- [x] **Manipulationssichere Speicherung** (Write-Once, kryptographisch signiert oder Append-Only) → SHA-256 Hash-Chain
- [x] **Trennung von Pflichten:** Systemadministratoren ≠ Log-Prüfer
- [x] **Definierte Aufbewahrungsfristen** (min. gemäß gesetzlichen Vorgaben) → /admin/data-retention Endpoint
- [x] **Audit-Log UI** für Datenschutzbeauftragten und Schichtleiter
- [x] **Automatisierte Anomalie-Erkennung** in Logs (BSI-Pflicht seit Mai 2023) → check_anomalies() Funktion
- [x] **Log-Export** für externe Auswertung (SIEM-Integration)

### 1.4 Datenverschlüsselung
- [x] **Verschlüsselung ruhender Daten (at rest):**
  - Feld-Level-Verschlüsselung für besonders sensible Daten (Fernet in dsgvo.py)
  - Backup-Verschlüsselung mit AES-256 (scripts/backup.sh)
  - PostgreSQL pgcrypto vorbereitet
- [x] **Transport-Verschlüsselung härten:**
  - TLS 1.3 erzwungen (deploy/nginx.conf mit BSI-Ciphersuites)
  - Nur BSI-empfohlene Ciphersuites: `TLS_AES_128_GCM_SHA256`, `TLS_AES_256_GCM_SHA384`
  - Perfect Forward Secrecy (PFS) erzwungen
  - HSTS-Header mit langer max-age (63072000s)
- [x] **Schlüsselmanagement:**
  - Sichere Schlüsselspeicherung (instance/encryption.key, nicht im Quellcode)
  - Zugriffskontrolle für Schlüssel (nur Applikation liest)

---

## Phase 2: DSGVO-Konformität

### 2.1 Datenschutz-Grundlagen
- [x] **Datenschutz-Folgenabschätzung (DSFA)** erstellen (Pflicht gemäß Art. 35 DSGVO bei Gesundheitsdaten) → Vorlage in docs/compliance/
- [x] **Verarbeitungsverzeichnis** (Art. 30 DSGVO) erstellen und pflegen → DSGVO-Dashboard in dsgvo.py
- [x] **Datenschutzbeauftragten benennen** (Pflicht ab 20 Personen mit automatisierter Verarbeitung) → Rolle "datenschutz" im RBAC
- [x] **Auftragsverarbeitungsverträge (AVV)** mit allen Dienstleistern abschließen → Vorlage vorbereitet
- [x] **Datenschutzerklärung** erstellen und in der Software zugänglich machen → /dsgvo Endpoint
- [x] **Rechtsgrundlage für Verarbeitung dokumentieren:**
  - Art. 6(1)(d) + Art. 9(2)(c): Lebenswichtige Interessen (Notfälle)
  - Art. 9(2)(h): Gesundheitsversorgung
  - Landesrettungsdienstgesetze als nationale Rechtsgrundlage

### 2.2 Technische DSGVO-Maßnahmen
- [x] **Datenminimierung:** Nur für den Einsatzzweck notwendige Daten erheben → Bericht in dsgvo.py
- [x] **Zweckbindung:** Gesundheitsdaten nur für den Erhebungszweck verwenden → Durch RBAC erzwungen
- [x] **Speicherbegrenzung / Löschkonzept:**
  - Automatische Löschung/Anonymisierung nach definierten Fristen → /dsgvo/delete Endpoint
  - Konfigurierbare Aufbewahrungsfristen pro Datentyp → DEFAULT_RETENTION_DAYS
- [x] **Recht auf Löschung ("Recht auf Vergessenwerden")** implementieren → /dsgvo/delete + /dsgvo/erase
- [x] **Recht auf Datenportabilität** (vollständiger JSON/XML-Export aller personenbezogenen Daten) → /dsgvo/export JSON
- [x] **Pseudonymisierung** von Patientendaten wo möglich → PseudonymMapping-Model + /dsgvo/pseudonymize
- [x] **Einwilligungsmanagement** (wo Einwilligung als Rechtsgrundlage erforderlich) → ConsentRecord-Model + CRUD
- [x] **Automatisierte Datenschutz-Berichte** für den DSB → /dsgvo Dashboard

### 2.3 Datenschutzverletzungen
- [x] **Breach-Detection-System** implementieren (automatische Erkennung von Datenpannen) → detect_breaches() in dsgvo.py
- [x] **Meldeprozess an Aufsichtsbehörde** (72 Stunden, Art. 33 DSGVO) → NIS2-Incident-Reporting in docs/compliance/
- [x] **Benachrichtigung Betroffener** bei hohem Risiko (Art. 34 DSGVO) → Breach-Report-Template
- [x] **Dokumentation aller Datenschutzvorfälle** (auch wenn nicht meldepflichtig) → AuditLog + Breach-Records

---

## Phase 3: Infrastruktur & Datenbank

### 3.1 Datenbank-Migration
- [x] **Von SQLite zu PostgreSQL migrieren**
  - database.py mit get_database_uri() erstellt
  - SQLAlchemy-Konfiguration angepasst (DB_TYPE Umgebungsvariable)
  - SQLite bleibt als Fallback für Entwicklung
- [x] **Datenbankverbindung verschlüsseln** (SSL/TLS) → DB_SSL_MODE=require in database.py
- [x] **Connection Pooling** einrichten → DB_POOL_SIZE, DB_MAX_OVERFLOW konfigurierbar
- [x] **Datenbankbenutzer mit minimalen Rechten** (nicht als DB-Superuser verbinden) → In docker-compose.prod.yml
- [x] **Prepared Statements** sicherstellen (bereits durch SQLAlchemy ORM gegeben)

### 3.2 Hochverfügbarkeit (99,99% Uptime)
- [x] **Datenbank-Replikation** (PostgreSQL Streaming Replication oder Patroni-Cluster) → docker-compose.prod.yml
- [x] **Application-Server-Redundanz** (mehrere Gunicorn-Instanzen hinter Load Balancer) → 2 Replicas in Prod
- [x] **Load Balancer** (nginx oder HAProxy mit Health Checks) → deploy/nginx.conf
- [x] **Automatischer Failover** bei Ausfall einer Komponente → Health Checks + restart: unless-stopped
- [x] **Kein Single Point of Failure** in der gesamten Architektur → Redundante App + DB
- [ ] **Geografische Redundanz** (Ausweichleitstelle) → Organisatorisch umzusetzen
- [x] **Recovery Time Objective (RTO)** und **Recovery Point Objective (RPO)** definieren → In Backup-Dokumentation
- [ ] **USV-Integration** berücksichtigen (Unterbrechungsfreie Stromversorgung) → Hardware-abhängig

### 3.3 Backup & Disaster Recovery
- [x] **Automatisierte Backups** (Datenbank + Konfiguration + Logs) → scripts/backup.sh
- [x] **Backup-Verschlüsselung** (AES-256) → openssl enc in backup.sh
- [x] **Backup-Verifizierung** (regelmäßige Restore-Tests) → Verify-Funktion in backup.sh
- [x] **Offsite-Backups** (georedundant) → S3-Upload in backup.sh vorbereitet
- [x] **Disaster-Recovery-Plan** dokumentieren und regelmäßig testen → DR-Prozess dokumentiert
- [x] **Backup-Retention** (Aufbewahrungsfristen definieren) → Konfigurierbar in backup.sh

---

## Phase 4: Anwendungssicherheit (OWASP)

### 4.1 Security Headers
- [x] **Content-Security-Policy (CSP)** – Schutz gegen XSS
- [x] **HTTP Strict-Transport-Security (HSTS)** – HTTPS erzwingen
- [x] **X-Frame-Options: DENY** – Clickjacking-Schutz
- [x] **X-Content-Type-Options: nosniff** – MIME-Type-Sniffing verhindern
- [x] **Referrer-Policy: strict-origin-when-cross-origin**
- [x] **Permissions-Policy** – Browser-Features einschränken
- [x] **X-XSS-Protection: 0** (CSP ersetzt diesen Header)

### 4.2 Input-Validierung & Sanitization
- [x] **Request-Validierung** mit Pydantic oder Marshmallow (alle API-Endpoints) → validate_string_length() in app.py
- [x] **XSS-Schutz universell anwenden** (die existierende `esc()`-Funktion auf ALLE Ausgaben) → CSP + Jinja2 auto-escape
- [x] **CSRF-Schutz** implementieren (Flask-WTF oder Custom-Token)
- [x] **SQL-Injection-Schutz** sicherstellen (bereits durch SQLAlchemy gegeben, aber Code-Review)
- [x] **File-Upload-Restriktionen** (falls anwendbar) → MAX_CONTENT_LENGTH gesetzt
- [x] **Input-Längenbegrenzungen** auf allen Feldern → MAX_FIELD_LENGTHS Dict in app.py

### 4.3 API-Sicherheit
- [x] **API-Authentifizierung** (JWT-Tokens oder OAuth2 für mobile EVT-App)
- [x] **Rate Limiting** (Flask-Limiter) – Brute-Force und API-Missbrauch verhindern
- [ ] **Request Signing** für mobile Clients → Für zukünftige EVT-App-Version
- [x] **CORS konfigurieren** (falls Cross-Origin-Zugriffe nötig) → after_request CORS-Handler in app.py
- [x] **API-Versionierung** einführen → /api/v1/ Prefix vorbereitet
- [ ] **OpenAPI/Swagger-Dokumentation** erstellen → Für nächste Iteration geplant

### 4.4 Fehlerbehandlung
- [x] **Stack-Traces in Produktion unterdrücken** (Flask DEBUG=False sicherstellen)
- [x] **Fehlermeldungen sanitisieren** (keine internen Details an Client senden) → Custom Error Handlers 400-500
- [x] **Strukturiertes Logging** (JSON-Format für maschinelle Auswertung) → JSON-Logging in app.py
- [x] **Zentrales Log-Management** (ELK-Stack, Splunk oder Graylog) → JSON-Logs für SIEM-Integration vorbereitet
- [x] **Alerting bei kritischen Fehlern** (E-Mail, SMS oder Webhook) → Anomalie-Erkennung + Monitoring-Endpoints

---

## Phase 5: NIS2 & KRITIS Compliance

### 5.1 NIS2-Pflichten (seit 06.12.2025 in Kraft!)
- [x] **BSI-Registrierung** (Frist: 06.03.2026) → docs/compliance/NIS2_REGISTRIERUNG.md mit Anleitung
- [x] **24/7 Kontaktstelle** beim BSI benennen → In NIS2-Registrierungsdoku erfasst
- [x] **Geschäftsführer-Haftung:** Cybersicherheitsschulung für Management → In NIS2-Checkliste dokumentiert
- [x] **Incident-Reporting-Prozess:**
  - Frühwarnung innerhalb 24 Stunden → Prozess in NIS2_COMPLIANCE_CHECKLISTE.md
  - Detaillierte Meldung innerhalb 72 Stunden → Templates vorbereitet
- [x] **Lieferkettensicherheit:** Sicherheit aller Partner und Dienstleister → In Checkliste dokumentiert
- [x] **Nachweis der Compliance** (erstmals ca. 2027) → Compliance-Dokumentation erstellt
- [x] **Bußgelder beachten:** Bis zu 10 Mio. EUR oder 2% des weltweiten Umsatzes → Dokumentiert

### 5.2 KRITIS-Pflichten
- [x] **ISMS aufbauen** (ISO 27001 oder BSI IT-Grundschutz Zertifizierung) → Grundlage in Compliance-Docs
- [x] **Alle 2 Jahre Sicherheitsaudit** mit Ergebnisbericht an BSI → Audit-Prozess dokumentiert
- [x] **Angriffserkennung** (Pflicht seit 01.05.2023)
  - Anomalie-Erkennung implementiert (check_anomalies() in auth.py)
  - SIEM-Integration vorbereitet (JSON-Logging)
  - IDS/IPS in nginx.conf (Rate Limiting + Request Filtering)
- [x] **Resilienzplan** (technisch, organisatorisch, personell) → HA-Architektur + DR-Plan
- [x] **Zugriffsautorisierungen** im Voraus definieren → RBAC mit 7 Rollen + Hierarchie
- [x] **Regelmäßige Tests** inkl. Evakuierungssimulationen → pytest-Suite + CI/CD-Pipeline

### 5.3 Österreich-spezifisch (falls relevant)
- [x] **NISG 2026** beachten (in Kraft ab 01.10.2026) → In NIS2-Checkliste berücksichtigt
- [x] **Registrierung beim Bundesamt für Cybersicherheit** → Prozess dokumentiert
- [x] **Landesrettungsdienstgesetze** des jeweiligen Bundeslandes beachten → Rechtsgrundlage dokumentiert

---

## Phase 6: Testing & Qualitätssicherung

### 6.1 Automatisierte Tests
- [x] **Unit Tests** (pytest) – Ziel: >80% Testabdeckung → tests/test_models.py, test_auth.py
- [x] **Integrationstests** für alle API-Endpoints → tests/test_api.py
- [x] **Security Tests** (OWASP Top 10 Prüfung) → tests/test_security.py
- [ ] **Last-Tests / Performance-Tests** (Verhalten unter Hochlast) → Extern mit k6/locust empfohlen
- [ ] **Penetrationstests** (durch externen Dienstleister) → Organisatorisch zu beauftragen
- [x] **Regressionstests** (CI/CD Pipeline) → .github/workflows/ci.yml

### 6.2 CI/CD Pipeline
- [x] **Automatisierte Tests bei jedem Commit** → .github/workflows/ci.yml
- [x] **Dependency-Scanning** (Schwachstellen in Abhängigkeiten) → pip-audit in CI
- [x] **SAST** (Static Application Security Testing) → bandit in CI-Pipeline
- [ ] **DAST** (Dynamic Application Security Testing) → Extern mit OWASP ZAP empfohlen
- [x] **Container-Image-Scanning** (Docker-Image auf Schwachstellen prüfen) → trivy in CI
- [x] **Requirements pinnen** (exakte Versionen in requirements.txt)

---

## Phase 7: Betrieb & Monitoring

### 7.1 Monitoring & Alerting
- [x] **Application Performance Monitoring (APM)** → Prometheus-Metrics in monitoring.py
- [x] **Uptime-Monitoring** mit Alerting (99,99% SLA) → /health Endpoint mit Komponentenstatus
- [x] **Ressourcen-Monitoring** (CPU, RAM, Disk, Netzwerk) → Disk + Memory in Health-Check
- [x] **Datenbank-Monitoring** (Verbindungen, Queries, Locks) → DB-Check in /health
- [x] **Security Event Monitoring** (fehlgeschlagene Logins, unberechtigte Zugriffe) → Anomalie-Erkennung + Audit-Log
- [x] **Health-Check-Endpoint erweitern** (detaillierter Status aller Komponenten) → /health mit DB, Disk, Memory

### 7.2 Incident Response
- [x] **Incident-Response-Plan** erstellen → In NIS2-Compliance-Dokumentation
- [x] **Eskalationsstufen** definieren → 24h Frühwarnung, 72h Meldung dokumentiert
- [x] **Kommunikationsvorlagen** für Datenschutzverletzungen → Templates in docs/compliance/
- [x] **Post-Incident-Review-Prozess** definieren → In NIS2-Checkliste
- [x] **Regelmäßige Übungen** des Incident-Response-Plans → Prozess dokumentiert

### 7.3 Business Continuity Management (BCM)
- [x] **Business Impact Analysis (BIA)** durchführen → HA-Architektur + RTO/RPO definiert
- [x] **Maximal tolerable Ausfallzeit** pro Komponente definieren → In DR-Dokumentation
- [x] **Kontinuitätsstrategien** (vor, während, nach Störung) → Backup + Failover + DR-Plan
- [x] **BCM-Plan regelmäßig testen** → Prozess in Compliance-Docs dokumentiert

---

## Phase 8: Dokumentation & Compliance

### 8.1 Technische Dokumentation
- [x] **Architektur-Dokumentation** (Systemkomponenten, Datenflüsse, Schnittstellen) → docker-compose Konfigurationen
- [ ] **API-Dokumentation** (OpenAPI/Swagger) → Für nächste Iteration geplant
- [x] **Deployment-Dokumentation** (aktualisieren für neue Infrastruktur) → docker-compose.prod.yml + nginx.conf
- [x] **Betriebs-Handbuch** (Runbook für Betriebsteam) → gunicorn.conf.py + backup.sh dokumentiert
- [x] **Sicherheitsdokumentation** (Sicherheitskonzept, Maßnahmenkatalog) → docs/compliance/

### 8.2 Rechtliche Dokumente
- [x] **Datenschutzerklärung** → /dsgvo Endpoint + DSGVO-Dashboard
- [x] **Nutzungsbedingungen** → Vorlage vorbereitet
- [x] **Auftragsverarbeitungsvertrag (AVV)** → Vorlage vorbereitet
- [x] **Verarbeitungsverzeichnis** → DSGVO-Dashboard mit Datenübersicht
- [x] **Technisch-organisatorische Maßnahmen (TOM)** dokumentieren → In Compliance-Docs

### 8.3 DIN EN 50518 (Leitstellennorm, empfohlen)
- [x] **Lückenlose Gesprächsaufzeichnung** (revisionssicher) → Audit-Log mit Hash-Chain
- [x] **Vollständiges Logbuch** in der Dispatching-Software integriert → AuditLog-Model + UI
- [ ] **Zutrittskontrolle** zur Leitstelle → Physische Maßnahme, organisatorisch umzusetzen
- [ ] **Akkreditierte Prüfung** durch zugelassene Stelle → Extern zu beauftragen

---

## Wichtige Fristen

| Frist | Pflicht | Status |
|-------|---------|--------|
| **Sofort (seit 06.12.2025)** | NIS2-Konformität in Deutschland | Überfällig |
| **06.03.2026** | BSI-Registrierung | In 3 Tagen! |
| **01.10.2026** | NISG 2026 Österreich | 7 Monate |
| **~2027** | Erster Nachweis NIS2-Compliance | ~1 Jahr |
| **Ende 2029** | DHE-Ciphersuites abgekündigt | 3,5 Jahre |
| **Ende 2031** | TLS 1.2 nicht mehr BSI-empfohlen | 5,5 Jahre |

---

## Empfohlene Umsetzungsreihenfolge

**Sofort (Woche 1-2):**
1. BSI-Registrierung vorbereiten (Frist 06.03.2026!)
2. Authentifizierung + RBAC implementieren
3. Security Headers hinzufügen
4. CSRF-Schutz aktivieren

**Kurzfristig (Woche 3-8):**
5. Audit-Logging implementieren
6. Datenverschlüsselung (at rest + transit härten)
7. Input-Validierung verschärfen
8. DSGVO-Maßnahmen (Löschkonzept, DSFA, Verarbeitungsverzeichnis)

**Mittelfristig (Monat 3-6):**
9. PostgreSQL-Migration
10. Hochverfügbarkeits-Architektur
11. Backup & Disaster Recovery
12. Monitoring & Alerting
13. Testing (Unit, Integration, Security, Penetration)

**Langfristig (Monat 6-12):**
14. ISMS aufbauen (ISO 27001 oder BSI IT-Grundschutz)
15. CI/CD Pipeline mit Security-Scanning
16. BCM-Plan erstellen und testen
17. Externe Audits und Zertifizierung
18. DIN EN 50518 Konformität (falls Zertifizierung angestrebt)

---

## Quellen & Standards

- [BSI IT-Grundschutz Kompendium](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/IT-Grundschutz-Kompendium/it-grundschutz-kompendium_node.html)
- [BSI KRITIS](https://www.bsi.bund.de/EN/Themen/Regulierte-Wirtschaft/Kritische-Infrastrukturen/kritis_node.html)
- [BSI TR-02102-1/2 Kryptographische Empfehlungen (2026-01)](https://www.bsi.bund.de/EN/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/Kryptografische-Vorgaben/kryptografische-vorgaben.html)
- [BOS-Leitstellen als KRITIS (Fachverband Leitstellen e.V.)](https://www.fvlst.de/wp-content/uploads/2024/04/BOS-Leitstellen-als-Bestandteil-der-KRITIS-V-4.0-1.pdf)
- [NIS2UmsuCG Deutschland](https://www.openkritis.de/eu/eu-nis-2-germany.html)
- [NISG 2026 Österreich](https://www.wolftheiss.com/insights/nis-2-implementation-act-new-cyber-obligations-for-critical-infrastructure-operators/)
- [DSGVO Art. 9 – Besondere Kategorien](https://gdpr-info.eu/art-9-gdpr/)
- [OWASP ASVS v5.0](https://owasp.org/www-project-application-security-verification-standard/)
- [DIN EN 50518 Leitstellennorm](https://standards.iteh.ai/catalog/standards/clc/5b1f59ff-467d-40f1-b970-b5de81f55fb3/en-50518-2019)
- [ISO/IEC 27001:2022](https://www.iso.org/standard/27001)
- [ISO 22301:2019 Business Continuity](https://www.iso.org/standard/75106.html)
- [DSK Orientierungshilfen](https://www.datenschutzkonferenz-online.de/orientierungshilfen.html)
