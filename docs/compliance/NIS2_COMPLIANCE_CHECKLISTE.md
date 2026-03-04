# NIS2 Compliance-Checkliste

## OpMan-GPT -- Einsatzleitsoftware

| Feld | Wert |
|------|------|
| Dokumenttyp | Compliance-Checkliste |
| Version | 1.0 |
| Erstellt | 04.03.2026 |
| Verantwortlich | Geschaeftsfuehrung / IT-Sicherheitsbeauftragter |
| Naechste Pruefung | 04.06.2026 |
| Klassifizierung | Intern / Vertraulich |

---

## 1. Registrierung und Meldepflichten

### 1.1 Registrierung beim BSI

- [ ] Betroffenheitsanalyse durchgefuehrt
- [ ] Registrierung beim BSI abgeschlossen (Frist: **06.03.2026**)
- [ ] BSI-Referenznummer erhalten: ________________
- [ ] Kontaktstelle benannt und gemeldet
- [ ] 24/7-Erreichbarkeit der Kontaktstelle sichergestellt
- [ ] Aenderungen an Registrierungsdaten innerhalb von 2 Wochen gemeldet

### 1.2 Meldepflichten bei Sicherheitsvorfaellen

#### Zeitplan fuer Vorfallmeldungen

| Stufe | Frist | Inhalt | Status |
|-------|-------|--------|--------|
| Fruehwarnung | **24 Stunden** nach Kenntnis | Verdacht auf erheblichen Sicherheitsvorfall, ob grenzueberschreitend | [ ] Prozess etabliert |
| Vorfallmeldung | **72 Stunden** nach Kenntnis | Bewertung, Schweregrad, Auswirkungen, Kompromittierungsindikatoren | [ ] Prozess etabliert |
| Zwischenbericht | Auf BSI-Anfrage | Aktueller Stand, Massnahmen | [ ] Prozess etabliert |
| Abschlussbericht | **1 Monat** nach Vorfallmeldung | Vollstaendige Beschreibung, Ursache, Massnahmen, grenzueberschreitende Auswirkungen | [ ] Prozess etabliert |

#### Meldeprozess-Checkliste

- [ ] Meldeformulare vorbereitet (BSI-Portal)
- [ ] Verantwortlichkeiten fuer Meldungen definiert
- [ ] Eskalationspfade dokumentiert
- [ ] Meldeablauf regelmaessig geuebt (mindestens 1x jaehrlich)
- [ ] Kontaktdaten BSI CERT-Bund aktuell: cert@bsi.bund.de
- [ ] Sichere Kommunikationskanaele zum BSI eingerichtet
- [ ] Interne Dokumentation aller Vorfaelle sichergestellt

---

## 2. Risikomanagement (Art. 21 NIS2)

### 2.1 Risikoanalyse

- [ ] Systematische Risikoanalyse durchgefuehrt
- [ ] Bedrohungen identifiziert und bewertet
- [ ] Schwachstellen identifiziert und bewertet
- [ ] Risikobehandlungsplan erstellt
- [ ] Restrisiken dokumentiert und von Geschaeftsfuehrung akzeptiert
- [ ] Regelmaessige Aktualisierung (mindestens jaehrlich)

### 2.2 Technische Sicherheitsmassnahmen

- [ ] Konzept fuer Risikoanalyse und Informationssicherheit
- [ ] Bewaeltigung von Sicherheitsvorfaellen (Incident Response)
- [ ] Aufrechterhaltung des Betriebs (BCM) und Krisenmanagement
- [ ] Sicherheit der Lieferkette
- [ ] Sicherheit bei Erwerb, Entwicklung und Wartung von IT-Systemen
- [ ] Konzepte und Verfahren zur Bewertung der Wirksamkeit von Massnahmen
- [ ] Grundlegende Cyberhygiene und Schulungen
- [ ] Konzepte fuer Kryptographie und Verschluesselung
- [ ] Sicherheit des Personals und Zugangskontrollen
- [ ] Multi-Faktor-Authentifizierung (MFA) oder kontinuierliche Authentifizierung

### 2.3 OpMan-GPT-spezifische Massnahmen

| Massnahme | Implementiert | Nachweis |
|-----------|:------------:|----------|
| Rollenbasierte Zugriffskontrolle (RBAC) | Ja | models.py: ROLES, ROLE_HIERARCHY |
| Multi-Faktor-Authentifizierung (TOTP) | Ja | models.py: mfa_secret, mfa_enabled |
| Brute-Force-Schutz (Account-Sperrung) | Ja | auth.py: MAX_FAILED_LOGINS, LOCKOUT_MINUTES |
| Revisionssichere Audit-Logs (Hash-Chain) | Ja | auth.py: _compute_audit_hash() |
| Feld-Level-Verschluesselung (Fernet/AES) | Ja | dsgvo.py: encrypt_field(), decrypt_field() |
| CSRF-Schutz | Ja | app.py: CSRFProtect |
| Rate Limiting | Ja | app.py: Flask-Limiter |
| Session-Management mit Timeout | Ja | auth.py: SESSION_LIFETIME_MINUTES |
| Anomalie-Erkennung | Ja | auth.py: check_anomalies() |
| Break-Glass-Notfallzugang | Ja | auth.py: admin_break_glass() |
| DSGVO-Compliance-Modul | Ja | dsgvo.py: Blueprint |
| Gesundheits-Monitoring | Ja | monitoring.py: /health, /metrics |
| Datenloeschung/Anonymisierung | Ja | dsgvo.py: auto_cleanup() |
| Pseudonymisierung | Ja | dsgvo.py: pseudonymize_case() |
| Breach-Erkennung | Ja | dsgvo.py: check_breach() |

---

## 3. Geschaeftsfuehrer-Haftung

### 3.1 Persoenliche Haftung der Geschaeftsfuehrung

Die NIS2-Richtlinie fuehrt eine **persoenliche Haftung der Geschaeftsfuehrung** ein. Leitungsorgane koennen persoenlich haftbar gemacht werden, wenn sie ihren Pflichten nicht nachkommen.

#### Pflichten der Geschaeftsfuehrung

- [ ] **Genehmigung** der Risikomanagement-Massnahmen
- [ ] **Ueberwachung** der Umsetzung der Massnahmen
- [ ] **Teilnahme** an Cybersicherheitsschulungen (persoenlich, mindestens jaehrlich)
- [ ] **Haftungsuebernahme** bei Verstoessen gegen NIS2-Pflichten
- [ ] **Budget-Freigabe** fuer angemessene Sicherheitsmassnahmen
- [ ] **Ernennung** eines IT-Sicherheitsbeauftragten
- [ ] **Regelmaessige Berichterstattung** ueber Sicherheitslage anfordern

#### Nachweisdokumentation

| Nachweis | Datum | Unterschrift |
|----------|-------|-------------|
| Risikoanalyse genehmigt | __________ | __________ |
| Sicherheitsstrategie genehmigt | __________ | __________ |
| Budget freigegeben | __________ | __________ |
| Schulung absolviert | __________ | __________ |
| Jahresbericht Sicherheit zur Kenntnis genommen | __________ | __________ |

### 3.2 Haftungsrisiken

| Verstoss | Konsequenz |
|----------|-----------|
| Keine Risikomanagement-Massnahmen | Persoenliche Haftung, bis zu 2% des weltweiten Jahresumsatzes |
| Keine Vorfallmeldung | Bussgeld bis zu 10 Mio. EUR |
| Keine Schulungsteilnahme | Ordnungswidrigkeit, ggf. Abberufung |
| Fehlende Genehmigung | Geschaeftsfuehrer haftet persoenlich fuer entstandene Schaeden |

---

## 4. Sicherheit der Lieferkette

### 4.1 Bewertung der Lieferkette

| Lieferant/Dienstleister | Dienst | Risikobewertung | Vertrag geprueft | NIS2-konform |
|------------------------|--------|:---------------:|:----------------:|:------------:|
| Python Software Foundation | Python Runtime | Niedrig | N/A (Open Source) | -- |
| Pallets Projects | Flask Framework | Niedrig | N/A (Open Source) | -- |
| OpenStreetMap Foundation | Kartenkacheln | Niedrig | Nutzungsbedingungen | -- |
| [Hosting-Provider] | Server-Infrastruktur | Hoch | [ ] | [ ] |
| [TLS-Zertifikatsanbieter] | Zertifikate | Mittel | [ ] | [ ] |
| [Betriebssystem-Anbieter] | OS, Patches | Hoch | [ ] | [ ] |

### 4.2 Anforderungen an Lieferanten

- [ ] Sicherheitsanforderungen vertraglich festgelegt
- [ ] Regelmaessige Sicherheitsbewertung der Lieferanten
- [ ] Meldepflichten fuer Sicherheitsvorfaelle vertraglich vereinbart
- [ ] Audit-Rechte vertraglich gesichert
- [ ] Abhaengigkeiten von Lieferanten dokumentiert
- [ ] Notfallplaene fuer Ausfall von Lieferanten vorhanden
- [ ] Subunternehmer-Kette transparent

---

## 5. Schulungen und Awareness

### 5.1 Pflichtschulungen

| Zielgruppe | Thema | Haeufigkeit | Letzte Durchfuehrung | Naechste |
|------------|-------|:-----------:|:--------------------:|:--------:|
| Geschaeftsfuehrung | NIS2-Pflichten und Haftung | Jaehrlich | __________ | __________ |
| IT-Administratoren | Technische Sicherheitsmassnahmen | Halbjaehrlich | __________ | __________ |
| Disponenten/Leitstellenpersonal | Cyberhygiene und Vorfallmeldung | Jaehrlich | __________ | __________ |
| Alle Mitarbeiter | Phishing, Passwortsicherheit | Jaehrlich | __________ | __________ |
| IT-Sicherheitsbeauftragter | ISMS, Incident Response | Quartalsweise | __________ | __________ |

### 5.2 Schulungsnachweis

- [ ] Schulungskonzept erstellt
- [ ] Teilnehmerlisten gefuehrt
- [ ] Wirksamkeit der Schulungen ueberprueft
- [ ] Schulungsmaterialien aktuell gehalten

---

## 6. Sanktionen und Bussgelder

### 6.1 Bussgeldrahmen fuer wesentliche Einrichtungen

| Verstoss | Bussgeld |
|----------|----------|
| Nicht-Umsetzung der Risikomanagement-Massnahmen | **Bis zu 10 Mio. EUR** oder 2% des weltweiten Jahresumsatzes |
| Verstoss gegen Meldepflichten | **Bis zu 10 Mio. EUR** oder 2% des weltweiten Jahresumsatzes |
| Unterlassene Registrierung | **Bis zu 10 Mio. EUR** oder 2% des weltweiten Jahresumsatzes |
| Behinderung von Aufsichtsmassnahmen | **Bis zu 10 Mio. EUR** oder 2% des weltweiten Jahresumsatzes |

### 6.2 Zusaetzliche Sanktionen

- Voruebergehende Aussetzung von Zertifizierungen
- Voruebergehendes Verbot fuer Leitungspersonen
- Oeffentliche Bekanntmachung von Verstoessen ("Naming and Shaming")
- Anordnung von Abhilfemassnahmen durch die Aufsichtsbehoerde

---

## 7. Aufsicht und Pruefungen

### 7.1 Aufsichtsbehoerde

- **Wesentliche Einrichtungen**: Proaktive Aufsicht durch das BSI
- Das BSI kann **jederzeit** Vor-Ort-Inspektionen durchfuehren
- **Regelmaessige und anlassbezogene** Sicherheitsaudits
- **Ad-hoc-Audits** bei Sicherheitsvorfaellen

### 7.2 Pruefungsvorbereitung

- [ ] Dokumentation vollstaendig und aktuell
- [ ] ISMS-Dokumentation verfuegbar
- [ ] Incident-Response-Plan aktuell
- [ ] BCM-Plan aktuell
- [ ] Letzte Risikobewertung nicht aelter als 12 Monate
- [ ] Schulungsnachweise verfuegbar
- [ ] Audit-Logs verfuegbar und integer
- [ ] Technische Massnahmen nachweisbar

---

## 8. Zeitplan und Meilensteine

| Meilenstein | Termin | Status |
|-------------|--------|--------|
| BSI-Registrierung | 06.03.2026 | [ ] |
| Kontaktstelle operativ | 06.03.2026 | [ ] |
| Risikoanalyse abgeschlossen | 06.06.2026 | [ ] |
| ISMS-Konzept fertiggestellt | 06.09.2026 | [ ] |
| Incident-Response-Prozess etabliert | 06.06.2026 | [ ] |
| BCM-Plan fertiggestellt | 06.09.2026 | [ ] |
| Lieferkettenbewertung abgeschlossen | 06.09.2026 | [ ] |
| Erste Geschaeftsfuehrer-Schulung | 06.04.2026 | [ ] |
| ISMS-Implementierung | 06.03.2027 | [ ] |
| Erste externe Pruefung | 06.03.2028 | [ ] |

---

## 9. Dokumentenverweise

| Dokument | Pfad |
|----------|------|
| NIS2-Registrierung | docs/compliance/NIS2_REGISTRIERUNG.md |
| KRITIS-Massnahmen | docs/compliance/KRITIS_MASSNAHMEN.md |
| ISMS-Leitfaden | docs/compliance/ISMS_LEITFADEN.md |
| DSFA | docs/datenschutz/DSFA.md |
| Incident Response Plan | docs/betrieb/INCIDENT_RESPONSE_PLAN.md |
| BCM-Plan | docs/betrieb/BCM_PLAN.md |
| Sicherheitskonzept | docs/betrieb/SICHERHEITSKONZEPT.md |
| TOM | docs/datenschutz/TOM.md |

---

*Dieses Dokument ist mindestens quartalsweise zu ueberpruefen und bei Aenderungen der Rechtslage unverzueglich zu aktualisieren.*
