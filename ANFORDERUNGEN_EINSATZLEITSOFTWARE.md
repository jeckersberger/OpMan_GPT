# Anforderungsliste: Von Übungssoftware zur produktionsreifen Einsatzleitsoftware

> **Stand:** 03.03.2026
> **Basis:** BSI IT-Grundschutz, KRITIS, NIS2UmsuCG, DSGVO, ISO 27001, DIN EN 50518, OWASP ASVS v5.0
> **Aktueller Status:** ~15% produktionsreif (nur als Übungssoftware geeignet)

---

## Übersicht: Was fehlt?

| Bereich | Aktueller Status | Ziel |
|---------|-----------------|------|
| Authentifizierung | Keine | MFA + RBAC |
| Verschlüsselung (Daten in Ruhe) | Keine | AES-256 |
| Verschlüsselung (Transport) | TLS vorhanden | TLS 1.3 mit BSI-Ciphersuites |
| Audit-Logging | Keines | Revisionssichere Protokollierung |
| Zugriffskontrolle | Keine | Rollenbasiert (RBAC) |
| Datenschutz (DSGVO) | Nicht konform | Vollständige Konformität |
| Verfügbarkeit | Single Instance | 99,99% (max. 52,6 Min/Jahr Ausfall) |
| Datenbank | SQLite | PostgreSQL mit Replikation |
| Angriffserkennung | Keine | Pflicht seit Mai 2023 |
| Tests | Keine | >80% Testabdeckung |
| Incident Response | Keines | 24h Frühwarnung, 72h Meldung |

---

## Phase 1: Kritische Sicherheitslücken schließen

### 1.1 Authentifizierung & Benutzerverwaltung
- [x] **User-Model erstellen** (Benutzername, Passwort-Hash, Rolle, MFA-Secret, letzter Login, gesperrt, erstellt_am)
- [x] **Login-System implementieren** (Flask-Login oder Flask-OIDC)
- [x] **Passwort-Hashing** mit bcrypt/argon2 (BSI-konform)
- [ ] **Multi-Faktor-Authentifizierung (MFA)** für alle Benutzer (TOTP oder WebAuthn/FIDO2)
- [x] **Passwort-Richtlinien** gemäß BSI-Empfehlungen (Mindestlänge, Komplexität)
- [x] **Session-Management** mit sicheren Cookies (HttpOnly, Secure, SameSite=Strict)
- [x] **Session-Timeout** (15-30 Min für Disponenten, konfigurierbar)
- [ ] **Gleichzeitige Sessions begrenzen** (max. 1 aktive Session pro Benutzer)
- [x] **Brute-Force-Schutz** (Account-Sperrung nach X Fehlversuchen)
- [x] **Passwort-Reset-Mechanismus** (sicherer Token-basierter Flow)
- [ ] **LDAP/Active Directory Anbindung** (Integration in bestehende Organisationsstruktur)

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
- [ ] **Funktionstrennung:** Kritische Operationen erfordern mehrere autorisierte Personen
- [ ] **Notfallzugang (Break-Glass):** Dokumentierte Ausnahmeprozeduren mit nachträglicher Prüfung
- [ ] **Regelmäßige Überprüfung** der Zugriffsrechte (automatische Reviews)
- [x] **Sofortige Rechtsentzug** bei Rollenwechsel oder Austritt

### 1.3 Revisionssichere Audit-Protokollierung
- [x] **AuditLog-Model erstellen** (user_id, aktion, ressource, ressource_id, vorher, nachher, zeitstempel, ip_adresse, user_agent)
- [x] **Alle Datenänderungen protokollieren** (CREATE, UPDATE, DELETE auf allen Modellen)
- [x] **Alle Login-Versuche protokollieren** (erfolgreich UND fehlgeschlagen)
- [ ] **Alle API-Zugriffe protokollieren** (Wer hat wann welche Daten abgerufen?)
- [ ] **Manipulationssichere Speicherung** (Write-Once, kryptographisch signiert oder Append-Only)
- [x] **Trennung von Pflichten:** Systemadministratoren ≠ Log-Prüfer
- [ ] **Definierte Aufbewahrungsfristen** (min. gemäß gesetzlichen Vorgaben)
- [x] **Audit-Log UI** für Datenschutzbeauftragten und Schichtleiter
- [ ] **Automatisierte Anomalie-Erkennung** in Logs (BSI-Pflicht seit Mai 2023)
- [x] **Log-Export** für externe Auswertung (SIEM-Integration)

### 1.4 Datenverschlüsselung
- [ ] **Verschlüsselung ruhender Daten (at rest):**
  - Datenbank-Verschlüsselung (PostgreSQL mit pgcrypto oder Transparent Data Encryption)
  - Feld-Level-Verschlüsselung für besonders sensible Daten (Patientennamen, Diagnosen)
  - Backup-Verschlüsselung mit AES-256
- [ ] **Transport-Verschlüsselung härten:**
  - TLS 1.3 erzwingen (TLS 1.2 nur bis Ende 2031 akzeptabel)
  - Nur BSI-empfohlene Ciphersuites: `TLS_AES_128_GCM_SHA256`, `TLS_AES_256_GCM_SHA384`
  - Perfect Forward Secrecy (PFS) erzwingen
  - HSTS-Header mit langer max-age
- [ ] **Schlüsselmanagement:**
  - Dokumentierte Schlüsselrotation
  - Sichere Schlüsselspeicherung (nicht im Quellcode)
  - Zugriffskontrolle für Schlüssel

---

## Phase 2: DSGVO-Konformität

### 2.1 Datenschutz-Grundlagen
- [ ] **Datenschutz-Folgenabschätzung (DSFA)** erstellen (Pflicht gemäß Art. 35 DSGVO bei Gesundheitsdaten)
- [ ] **Verarbeitungsverzeichnis** (Art. 30 DSGVO) erstellen und pflegen
- [ ] **Datenschutzbeauftragten benennen** (Pflicht ab 20 Personen mit automatisierter Verarbeitung)
- [ ] **Auftragsverarbeitungsverträge (AVV)** mit allen Dienstleistern abschließen
- [ ] **Datenschutzerklärung** erstellen und in der Software zugänglich machen
- [ ] **Rechtsgrundlage für Verarbeitung dokumentieren:**
  - Art. 6(1)(d) + Art. 9(2)(c): Lebenswichtige Interessen (Notfälle)
  - Art. 9(2)(h): Gesundheitsversorgung
  - Landesrettungsdienstgesetze als nationale Rechtsgrundlage

### 2.2 Technische DSGVO-Maßnahmen
- [ ] **Datenminimierung:** Nur für den Einsatzzweck notwendige Daten erheben
- [ ] **Zweckbindung:** Gesundheitsdaten nur für den Erhebungszweck verwenden
- [ ] **Speicherbegrenzung / Löschkonzept:**
  - Automatische Löschung/Anonymisierung nach definierten Fristen
  - Konfigurierbare Aufbewahrungsfristen pro Datentyp
- [ ] **Recht auf Löschung ("Recht auf Vergessenwerden")** implementieren
- [ ] **Recht auf Datenportabilität** (vollständiger JSON/XML-Export aller personenbezogenen Daten)
- [ ] **Pseudonymisierung** von Patientendaten wo möglich
- [ ] **Einwilligungsmanagement** (wo Einwilligung als Rechtsgrundlage erforderlich)
- [ ] **Automatisierte Datenschutz-Berichte** für den DSB

### 2.3 Datenschutzverletzungen
- [ ] **Breach-Detection-System** implementieren (automatische Erkennung von Datenpannen)
- [ ] **Meldeprozess an Aufsichtsbehörde** (72 Stunden, Art. 33 DSGVO)
- [ ] **Benachrichtigung Betroffener** bei hohem Risiko (Art. 34 DSGVO)
- [ ] **Dokumentation aller Datenschutzvorfälle** (auch wenn nicht meldepflichtig)

---

## Phase 3: Infrastruktur & Datenbank

### 3.1 Datenbank-Migration
- [ ] **Von SQLite zu PostgreSQL migrieren**
  - Migrationsskript erstellen
  - Datenintegrität bei Migration sicherstellen
  - SQLAlchemy-Konfiguration anpassen
- [ ] **Datenbankverbindung verschlüsseln** (SSL/TLS)
- [ ] **Connection Pooling** einrichten
- [ ] **Datenbankbenutzer mit minimalen Rechten** (nicht als DB-Superuser verbinden)
- [ ] **Prepared Statements** sicherstellen (bereits durch SQLAlchemy ORM gegeben)

### 3.2 Hochverfügbarkeit (99,99% Uptime)
- [ ] **Datenbank-Replikation** (PostgreSQL Streaming Replication oder Patroni-Cluster)
- [ ] **Application-Server-Redundanz** (mehrere Gunicorn-Instanzen hinter Load Balancer)
- [ ] **Load Balancer** (nginx oder HAProxy mit Health Checks)
- [ ] **Automatischer Failover** bei Ausfall einer Komponente
- [ ] **Kein Single Point of Failure** in der gesamten Architektur
- [ ] **Geografische Redundanz** (Ausweichleitstelle)
- [ ] **Recovery Time Objective (RTO)** und **Recovery Point Objective (RPO)** definieren
- [ ] **USV-Integration** berücksichtigen (Unterbrechungsfreie Stromversorgung)

### 3.3 Backup & Disaster Recovery
- [ ] **Automatisierte Backups** (Datenbank + Konfiguration + Logs)
- [ ] **Backup-Verschlüsselung** (AES-256)
- [ ] **Backup-Verifizierung** (regelmäßige Restore-Tests)
- [ ] **Offsite-Backups** (georedundant)
- [ ] **Disaster-Recovery-Plan** dokumentieren und regelmäßig testen
- [ ] **Backup-Retention** (Aufbewahrungsfristen definieren)

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
- [ ] **Request-Validierung** mit Pydantic oder Marshmallow (alle API-Endpoints)
- [ ] **XSS-Schutz universell anwenden** (die existierende `esc()`-Funktion auf ALLE Ausgaben)
- [x] **CSRF-Schutz** implementieren (Flask-WTF oder Custom-Token)
- [x] **SQL-Injection-Schutz** sicherstellen (bereits durch SQLAlchemy gegeben, aber Code-Review)
- [ ] **File-Upload-Restriktionen** (falls anwendbar)
- [ ] **Input-Längenbegrenzungen** auf allen Feldern

### 4.3 API-Sicherheit
- [x] **API-Authentifizierung** (JWT-Tokens oder OAuth2 für mobile EVT-App)
- [x] **Rate Limiting** (Flask-Limiter) – Brute-Force und API-Missbrauch verhindern
- [ ] **Request Signing** für mobile Clients
- [ ] **CORS konfigurieren** (falls Cross-Origin-Zugriffe nötig)
- [ ] **API-Versionierung** einführen
- [ ] **OpenAPI/Swagger-Dokumentation** erstellen

### 4.4 Fehlerbehandlung
- [x] **Stack-Traces in Produktion unterdrücken** (Flask DEBUG=False sicherstellen)
- [ ] **Fehlermeldungen sanitisieren** (keine internen Details an Client senden)
- [ ] **Strukturiertes Logging** (JSON-Format für maschinelle Auswertung)
- [ ] **Zentrales Log-Management** (ELK-Stack, Splunk oder Graylog)
- [ ] **Alerting bei kritischen Fehlern** (E-Mail, SMS oder Webhook)

---

## Phase 5: NIS2 & KRITIS Compliance

### 5.1 NIS2-Pflichten (seit 06.12.2025 in Kraft!)
- [ ] **BSI-Registrierung** (Frist: 06.03.2026 – in 3 Tagen!)
- [ ] **24/7 Kontaktstelle** beim BSI benennen
- [ ] **Geschäftsführer-Haftung:** Cybersicherheitsschulung für Management (alle 3 Jahre Pflicht)
- [ ] **Incident-Reporting-Prozess:**
  - Frühwarnung innerhalb 24 Stunden
  - Detaillierte Meldung innerhalb 72 Stunden
- [ ] **Lieferkettensicherheit:** Sicherheit aller Partner und Dienstleister verifizieren
- [ ] **Nachweis der Compliance** (erstmals ca. 2027)
- [ ] **Bußgelder beachten:** Bis zu 10 Mio. EUR oder 2% des weltweiten Umsatzes

### 5.2 KRITIS-Pflichten
- [ ] **ISMS aufbauen** (ISO 27001 oder BSI IT-Grundschutz Zertifizierung)
- [ ] **Alle 2 Jahre Sicherheitsaudit** mit Ergebnisbericht an BSI
- [ ] **Angriffserkennung** (Pflicht seit 01.05.2023)
  - IDS/IPS (Intrusion Detection/Prevention System)
  - SIEM-System (Security Information and Event Management)
  - Anomalie-Erkennung
- [ ] **Resilienzplan** (technisch, organisatorisch, personell) gemäß KRITIS-Dachgesetz
- [ ] **Zugriffsautorisierungen** im Voraus definieren
- [ ] **Regelmäßige Tests** inkl. Evakuierungssimulationen

### 5.3 Österreich-spezifisch (falls relevant)
- [ ] **NISG 2026** beachten (in Kraft ab 01.10.2026)
- [ ] **Registrierung beim Bundesamt für Cybersicherheit**
- [ ] **Landesrettungsdienstgesetze** des jeweiligen Bundeslandes beachten

---

## Phase 6: Testing & Qualitätssicherung

### 6.1 Automatisierte Tests
- [ ] **Unit Tests** (pytest) – Ziel: >80% Testabdeckung
- [ ] **Integrationstests** für alle API-Endpoints
- [ ] **Security Tests** (OWASP Top 10 Prüfung)
- [ ] **Last-Tests / Performance-Tests** (Verhalten unter Hochlast)
- [ ] **Penetrationstests** (durch externen Dienstleister)
- [ ] **Regressionstests** (CI/CD Pipeline)

### 6.2 CI/CD Pipeline
- [ ] **Automatisierte Tests bei jedem Commit**
- [ ] **Dependency-Scanning** (Schwachstellen in Abhängigkeiten)
- [ ] **SAST** (Static Application Security Testing)
- [ ] **DAST** (Dynamic Application Security Testing)
- [ ] **Container-Image-Scanning** (Docker-Image auf Schwachstellen prüfen)
- [ ] **Requirements pinnen** (exakte Versionen in requirements.txt)

---

## Phase 7: Betrieb & Monitoring

### 7.1 Monitoring & Alerting
- [ ] **Application Performance Monitoring (APM)**
- [ ] **Uptime-Monitoring** mit Alerting (99,99% SLA)
- [ ] **Ressourcen-Monitoring** (CPU, RAM, Disk, Netzwerk)
- [ ] **Datenbank-Monitoring** (Verbindungen, Queries, Locks)
- [ ] **Security Event Monitoring** (fehlgeschlagene Logins, unberechtigte Zugriffe)
- [ ] **Health-Check-Endpoint erweitern** (detaillierter Status aller Komponenten)

### 7.2 Incident Response
- [ ] **Incident-Response-Plan** erstellen
- [ ] **Eskalationsstufen** definieren
- [ ] **Kommunikationsvorlagen** für Datenschutzverletzungen
- [ ] **Post-Incident-Review-Prozess** definieren
- [ ] **Regelmäßige Übungen** des Incident-Response-Plans

### 7.3 Business Continuity Management (BCM)
- [ ] **Business Impact Analysis (BIA)** durchführen
- [ ] **Maximal tolerable Ausfallzeit** pro Komponente definieren
- [ ] **Kontinuitätsstrategien** (vor, während, nach Störung)
- [ ] **BCM-Plan regelmäßig testen**

---

## Phase 8: Dokumentation & Compliance

### 8.1 Technische Dokumentation
- [ ] **Architektur-Dokumentation** (Systemkomponenten, Datenflüsse, Schnittstellen)
- [ ] **API-Dokumentation** (OpenAPI/Swagger)
- [ ] **Deployment-Dokumentation** (aktualisieren für neue Infrastruktur)
- [ ] **Betriebs-Handbuch** (Runbook für Betriebsteam)
- [ ] **Sicherheitsdokumentation** (Sicherheitskonzept, Maßnahmenkatalog)

### 8.2 Rechtliche Dokumente
- [ ] **Datenschutzerklärung**
- [ ] **Nutzungsbedingungen**
- [ ] **Auftragsverarbeitungsvertrag (AVV)**
- [ ] **Verarbeitungsverzeichnis**
- [ ] **Technisch-organisatorische Maßnahmen (TOM)** dokumentieren

### 8.3 DIN EN 50518 (Leitstellennorm, empfohlen)
- [ ] **Lückenlose Gesprächsaufzeichnung** (revisionssicher)
- [ ] **Vollständiges Logbuch** in der Dispatching-Software integriert
- [ ] **Zutrittskontrolle** zur Leitstelle
- [ ] **Akkreditierte Prüfung** durch zugelassene Stelle

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
