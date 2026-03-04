# Sicherheitskonzept -- OpMan_GPT

**Dokument:** Sicherheitskonzept
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Vertraulich

---

## 1. Einleitung

Dieses Sicherheitskonzept beschreibt die Bedrohungslandschaft, implementierten Sicherheitsmassnahmen und Konfigurationsanforderungen fuer den Betrieb der Einsatzleitsoftware OpMan_GPT.

---

## 2. Bedrohungsmodell (Threat Model)

### 2.1 Systemgrenzen und Angriffsoberflaeche

```
Angriffsoberflaeche OpMan_GPT:

EXTERN                          INTERN
  |                               |
  |  [A1] Web-Interface           |  [A6] Datenbankzugriff
  |       (Port 5000/5443)        |       (SQLite-Datei)
  |                               |
  |  [A2] API-Endpunkte           |  [A7] Dateisystem
  |       (REST JSON)             |       (Schluessel, Config)
  |                               |
  |  [A3] EVT-Token-Auth          |  [A8] Betriebssystem
  |       (URL-Parameter)         |       (OS-Schwachstellen)
  |                               |
  |  [A4] Web-Push (VAPID)        |  [A9] Physischer Zugang
  |       (Outbound)              |       (Server, Geraete)
  |                               |
  |  [A5] GPS-Daten               |  [A10] Insider-Bedrohung
  |       (Geolocation API)       |        (autorisierte Benutzer)
```

### 2.2 Bedrohungskatalog (STRIDE)

| ID | Kategorie | Bedrohung | Angriffsoberflaeche | Risiko |
|----|-----------|----------|---------------------|--------|
| T1 | **S**poofing | Identitaetsdiebstahl (Login-Credentials) | A1, A3 | Hoch |
| T2 | **S**poofing | Session-Hijacking | A1, A2 | Mittel |
| T3 | **S**poofing | Gefaelschte GPS-Position | A5 | Niedrig |
| T4 | **T**ampering | Manipulation der Datenbank | A6 | Hoch |
| T5 | **T**ampering | Manipulation von Audit-Logs | A6 | Hoch |
| T6 | **T**ampering | CSRF-Angriff | A1 | Mittel |
| T7 | **T**ampering | SQL-Injection | A2 | Mittel |
| T8 | **R**epudiation | Abstreiten von Aktionen | A1, A2 | Mittel |
| T9 | **I**nformation Disclosure | Zugriff auf Patientendaten | A1, A2, A6 | Sehr hoch |
| T10 | **I**nformation Disclosure | Schluessel-Exfiltration | A7 | Sehr hoch |
| T11 | **I**nformation Disclosure | GPS-Tracking-Missbrauch | A5, A2 | Mittel |
| T12 | **D**enial of Service | DDoS-Angriff | A1, A2 | Mittel |
| T13 | **D**enial of Service | Resource Exhaustion | A2 | Mittel |
| T14 | **E**levation of Privilege | Privilege Escalation (RBAC-Umgehung) | A1, A2 | Hoch |
| T15 | **E**levation of Privilege | Break-Glass Missbrauch | A1 | Mittel |

### 2.3 Bedrohung-Gegenmassnahmen-Matrix

| Bedrohung | Gegenmassnahme | Status |
|-----------|---------------|--------|
| T1 Spoofing | bcrypt-Hashing, MFA (TOTP), Account-Sperrung | Implementiert |
| T2 Session-Hijacking | Secure Cookies, HttpOnly, SameSite, Session-Limiting | Implementiert |
| T3 GPS-Spoofing | Akzeptiertes Restrisiko (Browser-API-Limitierung) | Akzeptiert |
| T4 DB-Manipulation | Dateisystem-Berechtigungen, RBAC | Teilweise |
| T5 Log-Manipulation | Hash-Chain (SHA-256), separate Speicherung | Implementiert |
| T6 CSRF | Flask-WTF CSRFProtect | Implementiert |
| T7 SQL-Injection | SQLAlchemy ORM (parametrisierte Queries) | Implementiert |
| T8 Repudiation | Audit-Log mit Hash-Chain, IP-Logging | Implementiert |
| T9 Patientendaten-Zugriff | Fernet-Verschluesselung, RBAC, MFA | Implementiert |
| T10 Schluessel-Exfiltration | Dateiberechtigungen (empf.), HSM (optional) | Teilweise |
| T11 GPS-Missbrauch | RBAC (nur Leitstelle sieht GPS), Auto-Loeschung | Implementiert |
| T12 DDoS | Rate Limiting (Flask-Limiter), lokaler Betrieb | Implementiert |
| T13 Resource Exhaustion | Rate Limiting, Monitoring | Implementiert |
| T14 Privilege Escalation | RBAC mit Hierarchie, Access Review | Implementiert |
| T15 Break-Glass Missbrauch | Zeitlimit (1h), Audit-Log, Review-Pflicht | Implementiert |

---

## 3. Sicherheitsmassnahmen-Katalog

### 3.1 Netzwerksicherheit

| Massnahme | Beschreibung | Konfiguration |
|-----------|-------------|--------------|
| TLS-Verschluesselung | Alle Verbindungen ueber HTTPS | TLS 1.2+, BSI TR-02102 |
| Lokaler Betrieb | Kein Internet-Zugang erforderlich (ausser OSM-Kacheln) | LAN-only |
| Firewall | Host-basierte Firewall | Nur Port 5000/5443 offen |
| Netzwerk-Segmentierung | Leitstellennetz separieren | VLAN empfohlen |

### 3.2 Anwendungssicherheit

| Massnahme | Implementierung | Modul |
|-----------|----------------|-------|
| Eingabevalidierung | SQLAlchemy ORM, Flask request parsing | app.py |
| Ausgabe-Encoding | Jinja2 Auto-Escaping | Templates |
| CSRF-Schutz | Flask-WTF CSRFProtect | app.py |
| Rate Limiting | Flask-Limiter (Request/Minute) | app.py |
| Content Security Policy | HTTP-Header (empfohlen) | Nginx/App |
| Secure Headers | X-Frame-Options, X-Content-Type-Options | Nginx/App |

### 3.3 Identitaets- und Zugangsmanagement

| Massnahme | Details |
|-----------|---------|
| Passwort-Hashing | bcrypt mit automatischem Salt |
| Passwort-Mindestlaenge | 8 Zeichen (konfigurierbar) |
| MFA | TOTP (pyotp, kompatibel mit Google Authenticator etc.) |
| Session-Timeout | 30 Minuten Inaktivitaet |
| Session-Limiting | Maximal 1 aktive Session pro Benutzer |
| Account-Sperrung | Nach 5 Fehlversuchen, 15 Minuten Sperrzeit |
| RBAC | 7 Rollen mit hierarchischer Berechtigung |
| Access Review | Alle 90 Tage automatischer Report |
| Break-Glass | Notfallzugriff mit Begruendung, 1h Limit, Audit |

---

## 4. Schluesselmanagement

### 4.1 Uebersicht kryptografischer Schluessel

| Schluessel | Algorithmus | Zweck | Speicherort | Rotation |
|-----------|------------|-------|-------------|---------|
| Fernet-Key | AES-128-CBC + HMAC-SHA256 | Patientennamen-Verschluesselung | instance/encryption.key | Bei Kompromittierung |
| Flask Secret Key | Random Bytes | Session-Signierung | app.py / Umgebungsvariable | Bei Deployment |
| VAPID Private Key | ECDSA P-256 | Web-Push Authentifizierung | instance/vapid_keys.json | Bei Kompromittierung |
| VAPID Public Key | ECDSA P-256 | Web-Push Client-Registrierung | instance/vapid_keys.json | Zusammen mit Private Key |
| bcrypt Salt | Random (128 Bit) | Passwort-Hashing | In password_hash (pro User) | Bei jedem PW-Wechsel |
| TOTP Secret | Base32 (160 Bit) | MFA Token-Generierung | users.mfa_secret (DB) | Bei MFA-Reset |
| TLS-Zertifikat | RSA/ECDSA | HTTPS-Verbindung | instance/cert.pem, key.pem | Jaehrlich |

### 4.2 Schluessel-Schutz

| Massnahme | Empfehlung |
|-----------|-----------|
| Dateiberechtigungen | `chmod 600` fuer alle Schluessel-Dateien |
| Backup | Verschluesselte Kopie an separatem Standort |
| Zugangsbeschraenkung | Nur root und Anwendungsbenutzer |
| Rotation | Bei Verdacht auf Kompromittierung sofort |
| HSM | Fuer Produktivbetrieb empfohlen (Fernet-Key in HSM) |
| Nicht in Git | Alle Schluessel in .gitignore |

### 4.3 Schluessel-Rotation Prozess

1. Neuen Schluessel generieren
2. Bestehende verschluesselte Daten mit altem Schluessel entschluesseln
3. Daten mit neuem Schluessel verschluesseln
4. Alten Schluessel sicher vernichten
5. Vorgang im Audit-Log dokumentieren

---

## 5. TLS-Konfigurationsanforderungen (BSI TR-02102)

### 5.1 Empfohlene TLS-Konfiguration

| Parameter | Anforderung | Konfiguration |
|-----------|-------------|--------------|
| Minimale Version | TLS 1.2 | `ssl_protocols TLSv1.2 TLSv1.3;` |
| Empfohlene Version | TLS 1.3 | Bevorzugt |
| Cipher Suites (TLS 1.3) | TLS_AES_256_GCM_SHA384, TLS_AES_128_GCM_SHA256, TLS_CHACHA20_POLY1305_SHA256 | Standard |
| Cipher Suites (TLS 1.2) | ECDHE-ECDSA-AES256-GCM-SHA384, ECDHE-RSA-AES256-GCM-SHA384, ECDHE-ECDSA-AES128-GCM-SHA256, ECDHE-RSA-AES128-GCM-SHA256 | `ssl_ciphers` |
| Schluessellaenge RSA | Mindestens 2048 Bit | 3072 Bit empfohlen |
| Schluessellaenge ECDSA | Mindestens P-256 | P-384 empfohlen |
| Perfect Forward Secrecy | Erforderlich (ECDHE) | Ja |
| HSTS | Empfohlen | `Strict-Transport-Security: max-age=31536000` |
| OCSP Stapling | Empfohlen (bei oeffentl. CA) | |

### 5.2 Nginx-Konfiguration (Referenz)

```nginx
server {
    listen 443 ssl http2;
    server_name opman.local;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name opman.local;
    return 301 https://$host$request_uri;
}
```

---

## 6. Haertungsmassnahmen

### 6.1 Betriebssystem-Haertung

- [ ] Minimale Installation (nur notwendige Pakete)
- [ ] Automatische Sicherheitsupdates aktiviert
- [ ] Nicht benoetigte Dienste deaktiviert
- [ ] SSH nur mit Key-Authentifizierung
- [ ] root-Login deaktiviert
- [ ] Firewall konfiguriert (nur notwendige Ports)
- [ ] Festplattenverschluesselung (LUKS)
- [ ] Dateiberechtigungen restriktiv gesetzt
- [ ] SELinux/AppArmor aktiviert (falls verfuegbar)

### 6.2 Anwendungs-Haertung

- [ ] DEBUG-Modus deaktiviert
- [ ] SECRET_KEY aus sicherer Quelle (nicht Standard)
- [ ] Fehlerseiten keine Systeminformationen preisgeben
- [ ] Stack Traces nur in Log-Dateien (nicht an Client)
- [ ] Admin-Interface nicht oeffentlich erreichbar
- [ ] Rate Limiting aktiviert
- [ ] CORS restriktiv konfiguriert (falls noetig)

### 6.3 Datenbank-Haertung

**SQLite:**
- [ ] Datenbankdatei mit restriktiven Berechtigungen (640)
- [ ] WAL-Mode aktiviert
- [ ] Regelmaessig VACUUM ausfuehren

**PostgreSQL (falls verwendet):**
- [ ] SSL-Verbindung erzwingen (`sslmode=require`)
- [ ] Nur notwendige Benutzerrechte (kein Superuser)
- [ ] `pg_hba.conf` restriktiv konfiguriert
- [ ] Passwort-Authentifizierung (scram-sha-256)
- [ ] Connection Pooling konfiguriert

---

## 7. Schwachstellenmanagement

### 7.1 Patch-Management

| Kategorie | SLA | Verantwortlich |
|-----------|-----|---------------|
| Kritische Schwachstelle (CVSS >= 9.0) | 24 Stunden | IT-Admin |
| Hohe Schwachstelle (CVSS 7.0-8.9) | 7 Tage | IT-Admin |
| Mittlere Schwachstelle (CVSS 4.0-6.9) | 30 Tage | IT-Admin |
| Niedrige Schwachstelle (CVSS < 4.0) | Naechstes Wartungsfenster | IT-Admin |

### 7.2 Schwachstellen-Monitoring

- [ ] CVE-Datenbanken ueberwachen (NVD, BSI-CERT)
- [ ] Python-Abhaengigkeiten pruefen (`pip audit`)
- [ ] Betriebssystem-Updates pruefen
- [ ] Quartalsweise Schwachstellenscan
- [ ] Jaehrlicher Penetrationstest

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
