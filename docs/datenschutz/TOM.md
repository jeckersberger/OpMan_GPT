# Technisch-Organisatorische Massnahmen (TOM)

**Dokument:** TOM-Dokumentation gemaess Art. 32 DSGVO
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich

---

## 1. Vertraulichkeit (Art. 32 Abs. 1 lit. b DSGVO)

### 1.1 Zutrittskontrolle (physisch)

Massnahmen, die unbefugten Personen den Zutritt zu den Datenverarbeitungsanlagen verwehren:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Zutrittskontrollsystem | Elektronisches Schliessystem fuer Serverraum/Leitstelle | [ ] |
| Besucherregelung | Besucher nur in Begleitung, Eintrag im Besucherbuch | [ ] |
| Schluesselregelung | Dokumentierte Schluesselausgabe, Schluesselprotokoll | [ ] |
| Sicherheitsbereiche | Serverraum als separater Sicherheitsbereich | [ ] |
| Videoüberwachung | Eingangsbereich und Serverraum | [ ] |
| Alarmsystem | Einbruchmeldeanlage mit Aufschaltung | [ ] |

### 1.2 Zugangskontrolle (logisch)

Massnahmen, die unbefugte Nutzung der Datenverarbeitungssysteme verhindern:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Passwort-Authentifizierung | Mindestens 8 Zeichen, bcrypt-Hashing mit Salt | [x] Implementiert |
| Multi-Faktor-Authentifizierung | TOTP (pyotp) fuer alle Benutzer konfigurierbar | [x] Implementiert |
| Account-Sperrung | Automatisch nach 5 Fehlversuchen, 15 Min Sperrzeit | [x] Implementiert |
| Session-Management | Secure Cookies, HttpOnly, SameSite=Lax, Timeout 30 Min | [x] Implementiert |
| Session-Limiting | Nur eine aktive Session pro Benutzer | [x] Implementiert |
| CSRF-Schutz | Flask-WTF CSRFProtect fuer alle Formulare | [x] Implementiert |
| Rate Limiting | Flask-Limiter gegen Brute-Force und DoS | [x] Implementiert |
| Firewall | Host-Firewall (iptables/nftables) | [ ] Empfohlen |
| VPN | VPN-Zugang fuer Remote-Administration | [ ] Empfohlen |

### 1.3 Zugriffskontrolle

Massnahmen, die gewaehrleisten, dass Berechtigte nur auf die Daten zugreifen, fuer die sie berechtigt sind:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Rollenbasierte Zugriffskontrolle (RBAC) | 7 Rollen mit hierarchischer Berechtigung | [x] Implementiert |
| Rollenhierarchie | admin(100) > schichtleiter(80) > disponent(60) > datenschutz/aerztl_leiter(50) > evt_operator(30) > beobachter(10) | [x] Implementiert |
| Need-to-Know-Prinzip | Jede Rolle sieht nur notwendige Daten | [x] Implementiert |
| Break-Glass-Verfahren | Notfallzugriff mit Begruendungspflicht, zeitlich begrenzt (1h), Audit-Logging | [x] Implementiert |
| Access Review | Regelmaessige Zugriffsueberprufung alle 90 Tage | [x] Implementiert |
| Dateisystem-Berechtigungen | Restriktive Berechtigungen auf Datenbankdateien und Schluessel | [ ] Empfohlen |

### 1.4 Trennungskontrolle

Massnahmen zur getrennten Verarbeitung von Daten, die zu unterschiedlichen Zwecken erhoben wurden:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Logische Datentrennung | Separate Datenbanktabellen pro Datentyp | [x] Implementiert |
| Mandantentrennung | Trennung durch Uebungs-/Einsatzkontext | [x] Implementiert |
| Pseudonym-Mapping | Pseudonymzuordnung getrennt von Falldaten | [x] Implementiert |
| Umgebungstrennung | Produktiv- und Testumgebung getrennt | [ ] Empfohlen |

---

## 2. Integritaet (Art. 32 Abs. 1 lit. b DSGVO)

### 2.1 Weitergabekontrolle

Massnahmen, die gewaehrleisten, dass Daten bei der Uebertragung nicht unbefugt gelesen, kopiert oder veraendert werden:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| HTTPS/TLS | Verschluesselte Uebertragung aller Daten | [x] Implementiert |
| TLS-Konfiguration | TLS 1.2+ (BSI TR-02102 konform) | [x] Implementiert |
| Zertifikatspruefung | Selbstsigniertes Zertifikat (Empfehlung: PKI) | [x] Implementiert |
| Web-Push-Verschluesselung | VAPID-Protokoll mit Ende-zu-Ende-Verschluesselung | [x] Implementiert |
| Lokaler Betrieb | Kein Datentransfer ueber Internet (LAN only) | [x] Implementiert |
| Datenexport-Kontrolle | Nur autorisierte Rollen koennen Daten exportieren | [x] Implementiert |

### 2.2 Eingabekontrolle

Massnahmen zur Nachvollziehbarkeit, ob und von wem Daten eingegeben, veraendert oder entfernt wurden:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Audit-Logging | Alle Aktionen mit Zeitstempel, Benutzer, IP protokolliert | [x] Implementiert |
| Hash-Chain | SHA-256-Verkettung der Audit-Eintraege (Manipulationsschutz) | [x] Implementiert |
| API-Access-Logging | Alle API-Zugriffe automatisch protokolliert | [x] Implementiert |
| Anomalie-Erkennung | Neue IP, Zugriff ausserhalb Geschaeftszeiten | [x] Implementiert |
| Breach-Erkennung | Automatische Pruefung auf Datenpannen-Indikatoren | [x] Implementiert |

---

## 3. Verfuegbarkeit und Belastbarkeit (Art. 32 Abs. 1 lit. b, c DSGVO)

### 3.1 Verfuegbarkeitskontrolle

Massnahmen gegen zufaellige oder mutwillige Zerstoerung oder Verlust:

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Datensicherung | Regelmaessige Backups der SQLite-Datenbank | [ ] Empfohlen |
| Backup-Verschluesselung | Verschluesselung der Backup-Dateien | [ ] Empfohlen |
| Backup-Tests | Monatliche Restore-Tests | [ ] Empfohlen |
| USV | Unterbrechungsfreie Stromversorgung | [ ] Empfohlen |
| RAID | Redundante Festplatten im Server | [ ] Empfohlen |
| Monitoring | Health-Check (/health) und Prometheus-Metriken (/metrics) | [x] Implementiert |
| WAL-Mode | SQLite Write-Ahead-Logging fuer Concurrent Access | [x] Implementiert |
| Pool-Recycling | Datenbankverbindungs-Pooling und Recycling | [x] Implementiert |

### 3.2 Belastbarkeit

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Gunicorn | Multi-Worker WSGI-Server fuer Lastverteilung | [x] Konfiguriert |
| Rate Limiting | Schutz gegen Ueberlastung | [x] Implementiert |
| Connection Pooling | PostgreSQL-Pooling (konfigurierbar) | [x] Implementiert |
| Graceful Degradation | System bleibt auch bei Teilausfaellen nutzbar | [x] Design |

---

## 4. Verschluesselung und Pseudonymisierung (Art. 32 Abs. 1 lit. a DSGVO)

### 4.1 Verschluesselung

| Bereich | Verfahren | Details | Status |
|---------|----------|---------|--------|
| Transport | TLS 1.2+ | HTTPS fuer alle Verbindungen | [x] Implementiert |
| Feld-Verschluesselung | Fernet (AES-128-CBC) | Patientennamen verschluesselt gespeichert | [x] Implementiert |
| Passwort-Speicherung | bcrypt | Salt + Hash, Kosten-Faktor 12 | [x] Implementiert |
| Push-Nachrichten | VAPID/Web Push | Ende-zu-Ende-Verschluesselung | [x] Implementiert |
| Schluessel-Speicherung | Dateisystem | instance/encryption.key (Empfehlung: HSM) | [x] Implementiert |
| Festplattenverschluesselung | LUKS | Empfohlen fuer Server | [ ] Empfohlen |
| Backup-Verschluesselung | AES-256 | Fuer externe Backups | [ ] Empfohlen |

### 4.2 Pseudonymisierung

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Pseudonymisierungs-API | Patientennamen durch Pseudonyme (Patient-XXXXXX) ersetzbar | [x] Implementiert |
| Getrenntes Mapping | Pseudonym-Zuordnung in separater Tabelle | [x] Implementiert |
| Hash-basiert | Original wird als SHA-256-Hash gespeichert, nicht im Klartext | [x] Implementiert |
| Anonymisierung | Unwiderrufliche Loeschung personenbezogener Daten ("GELOESCHT") | [x] Implementiert |

---

## 5. Verfahren zur regelmaessigen Ueberpruefung (Art. 32 Abs. 1 lit. d DSGVO)

### 5.1 Regelmaessige Ueberpruefungen

| Pruefung | Turnus | Verantwortlich | Status |
|----------|--------|---------------|--------|
| Access Review | Alle 90 Tage | Administrator | [x] Implementiert (/api/admin/access-review) |
| Audit-Log-Pruefung | Woechentlich | IS-Beauftragter | [ ] Organisatorisch |
| Penetrationstest | Jaehrlich | Externer Pruefer | [ ] Geplant |
| Schwachstellenscan | Quartalsweise | IT-Leitung | [ ] Geplant |
| Backup-Restore-Test | Monatlich | IT-Leitung | [ ] Geplant |
| TOM-Review | Jaehrlich | DSB + ISB | [ ] Geplant |
| Breach-Check | Taeglich (automatisch) | System | [x] Implementiert |
| Datenminimierungsbericht | Quartalsweise | DSB | [x] Implementiert |

### 5.2 Incident Management

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Incident Response Plan | Definierter Prozess fuer Sicherheitsvorfaelle | [ ] Siehe INCIDENT_RESPONSE_PLAN.md |
| Meldekette | Intern + BSI/Aufsichtsbehoerde | [ ] Definiert |
| Forensische Sicherung | Prozess fuer Beweismittelsicherung | [ ] Geplant |
| Post-Incident Review | Lessons Learned nach Vorfaellen | [ ] Geplant |

### 5.3 Mitarbeiterschulungen

| Thema | Turnus | Zielgruppe |
|-------|--------|-----------|
| Datenschutz-Grundlagen | Jaehrlich | Alle Benutzer |
| IT-Sicherheit und Passwoerter | Jaehrlich | Alle Benutzer |
| DSGVO-Betroffenenrechte | Jaehrlich | Disponenten, Schichtleiter |
| Umgang mit Gesundheitsdaten | Jaehrlich | Alle mit Datenzugriff |
| Incident Response | Halbjaehrlich | IT-Personal, Schichtleiter |
| Phishing-Awareness | Quartalsweise | Alle Benutzer |

---

## 6. Auftragsverarbeitung (Art. 28 DSGVO)

### 6.1 Aktuelle Auftragsverarbeiter

OpMan_GPT wird grundsaetzlich lokal betrieben. Folgende Auftragsverarbeitungen bestehen:

| Auftragsverarbeiter | Leistung | AVV vorhanden? | Standort |
|-------------------|----------|----------------|----------|
| [Hosting-Anbieter] | Server-Hosting (falls extern) | [ ] | EU |
| [IT-Dienstleister] | Wartung / Support | [ ] | EU |
| Browser-Push-Dienste | Push-Zustellung (Google FCM, Mozilla) | Technisch unvermeidbar | USA/EU |

### 6.2 Anforderungen an Auftragsverarbeiter

- Auftragsverarbeitungsvertrag (AVV) gemaess Art. 28 DSGVO
- Nachweis technisch-organisatorischer Massnahmen
- Unterauftragsverarbeiter nur mit Genehmigung
- Auditrecht vereinbart
- Siehe AVV_VORLAGE.md

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
