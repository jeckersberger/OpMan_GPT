# NIS2-Compliance-Checkliste

**Dokument:** NIS2-Compliance-Checkliste fuer OpMan_GPT
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich
**Rechtsgrundlage:** NIS-2-Richtlinie (EU) 2022/2555, NIS2UmsuCG (DE)

---

## 1. Risikomanagement-Massnahmen (ss 30 BSIG)

### 1.1 Risikoanalyse

- [ ] Systematische Risikoanalyse fuer alle IT-Systeme durchgefuehrt
- [ ] Bedrohungslandschaft fuer Rettungsdienst-IT analysiert
- [ ] Risikobewertung dokumentiert (Eintrittswahrscheinlichkeit x Schadenshoehe)
- [ ] Risikobehandlungsplan erstellt
- [ ] Restrisiken identifiziert und von Geschaeftsfuehrung akzeptiert
- [ ] Regelmaessige Aktualisierung (mindestens jaehrlich) geplant

### 1.2 Sicherheitskonzept

- [ ] Informationssicherheitsleitlinie erstellt und von GF unterschrieben
- [ ] Sicherheitskonzept fuer OpMan_GPT dokumentiert
- [ ] Asset-Inventar gepflegt
- [ ] Klassifizierungsschema fuer Informationen definiert
- [ ] Sicherheitsziele (CIA) fuer jedes System festgelegt

### 1.3 Sicherheitsmassnahmen (Art. 21 NIS-2-RL)

#### a) Konzepte fuer Risikoanalyse und Sicherheit

- [ ] Risikoanalyse-Methodik festgelegt (z.B. ISO 27005, BSI-Standard 200-3)
- [ ] Regelmaessige Risikobewertung (mindestens jaehrlich)
- [ ] Dokumentation aller identifizierten Risiken

#### b) Bewaltigung von Sicherheitsvorfaellen

- [ ] Incident-Response-Plan vorhanden (siehe INCIDENT_RESPONSE_PLAN.md)
- [ ] Meldekette definiert (intern + BSI)
- [ ] Reaktionszeiten definiert
- [ ] Forensische Sicherung von Beweismitteln geregelt
- [ ] Post-Incident-Review etabliert

#### c) Business Continuity Management

- [ ] BCM-Plan vorhanden (siehe BCM_PLAN.md)
- [ ] Backup-Konzept implementiert
- [ ] Recovery-Ziele (RTO/RPO) definiert
- [ ] Krisenmanagement-Organisation benannt
- [ ] Notbetriebsverfahren dokumentiert

#### d) Sicherheit der Lieferkette

- [ ] Lieferantenverzeichnis gefuehrt
- [ ] Sicherheitsanforderungen in Vertraegen verankert
- [ ] Regelmaessige Ueberpruefung von Dienstleistern
- [ ] Abhaengigkeiten von Drittanbietern dokumentiert
- [ ] Patch-Management fuer Drittanbieter-Software

**Lieferanten-Uebersicht OpMan_GPT:**

| Lieferant / Abhaengigkeit | Art | Risikobewertung | Massnahme |
|---------------------------|-----|-----------------|-----------|
| Python / Flask Framework | Open Source | Mittel | Regelmaessige Updates, CVE-Monitoring |
| SQLAlchemy / SQLite | Open Source | Mittel | Regelmaessige Updates |
| Leaflet.js | Open Source (Client) | Niedrig | Lokale Einbindung |
| OpenStreetMap Kacheln | Externer Dienst | Niedrig | Offline-Kacheln vorhalten |
| pywebpush (VAPID) | Open Source | Niedrig | Regelmaessige Updates |
| Cryptography (Fernet) | Open Source | Hoch | CVE-Monitoring, zeitnahe Updates |
| Betriebssystem (Linux) | Open Source | Hoch | Haertung, Patch-Management |

#### e) Sicherheit bei Erwerb, Entwicklung und Wartung

- [ ] Secure Development Lifecycle (SDL) dokumentiert
- [ ] Code-Reviews durchgefuehrt
- [ ] Schwachstellenmanagement implementiert
- [ ] Aenderungsmanagement (Change Management) etabliert
- [ ] Test- und Produktionsumgebung getrennt

#### f) Konzepte fuer Bewertung der Wirksamkeit

- [ ] Regelmaessige Wirksamkeitspruefung der Sicherheitsmassnahmen
- [ ] Interne Audits geplant (mindestens jaehrlich)
- [ ] Penetrationstests (mindestens jaehrlich)
- [ ] Schwachstellenscans (mindestens quartalsweise)
- [ ] KPIs fuer Informationssicherheit definiert

#### g) Cyberhygiene und Schulungen

- [ ] Schulungsplan fuer alle Mitarbeiter erstellt
- [ ] Geschaeftsfuehrer-Schulung zu Cybersicherheit durchgefuehrt (ss 38 BSIG!)
- [ ] Awareness-Kampagnen durchgefuehrt
- [ ] Phishing-Simulationen geplant
- [ ] Passworrichtlinien implementiert und kommuniziert

#### h) Kryptografie und Verschluesselung

- [ ] Verschluesselungskonzept dokumentiert
- [ ] TLS/SSL fuer alle Verbindungen (BSI TR-02102 konform)
- [ ] Verschluesselung ruhender Daten (Fernet/AES in OpMan_GPT implementiert)
- [ ] Schluesselmanagement dokumentiert
- [ ] Kryptografische Algorithmen regelmaessig geprueft

#### i) Personalsicherheit und Zugangskontrollen

- [ ] RBAC implementiert (in OpMan_GPT vorhanden: 7 Rollen)
- [ ] Multi-Faktor-Authentifizierung (TOTP in OpMan_GPT implementiert)
- [ ] Passwortrichtlinien (mind. 8 Zeichen, in OpMan_GPT implementiert)
- [ ] Brute-Force-Schutz (Account-Sperrung in OpMan_GPT implementiert)
- [ ] Zugangsueberprufung (Access Review alle 90 Tage)
- [ ] Trennung von Aufgaben (Segregation of Duties)

#### j) Verwendung sicherer Kommunikation

- [ ] HTTPS fuer alle Web-Verbindungen
- [ ] Verschluesselte E-Mail-Kommunikation (PGP/S-MIME)
- [ ] Sichere Authentifizierung (Session-Management in OpMan_GPT)
- [ ] Schutz gegen CSRF (in OpMan_GPT implementiert)
- [ ] Rate Limiting implementiert (Flask-Limiter)

---

## 2. Geschaeftsfuehrer-Haftung (ss 38 BSIG)

### 2.1 Pflichten der Geschaeftsfuehrung

**WICHTIG: Die Geschaeftsfuehrung haftet persoenlich fuer die Einhaltung der NIS2-Pflichten!**

- [ ] Geschaeftsfuehrung hat Risikomanagement-Massnahmen gebilligt
- [ ] Geschaeftsfuehrung ueberwacht die Umsetzung der Massnahmen
- [ ] Geschaeftsfuehrung hat an Cybersicherheits-Schulung teilgenommen
- [ ] Dokumentation der GF-Entscheidungen vorhanden
- [ ] Haftungsrisiken identifiziert und (soweit moeglich) versichert

### 2.2 Schulungspflicht der Geschaeftsfuehrung

| Schulungsthema | Status | Datum | Nachweis |
|----------------|--------|-------|----------|
| NIS2-Grundlagen und Pflichten | [ ] Offen | ___.___._____ | |
| Cybersicherheits-Risikomanagement | [ ] Offen | ___.___._____ | |
| Incident Response und Meldepflichten | [ ] Offen | ___.___._____ | |
| Datenschutz und DSGVO | [ ] Offen | ___.___._____ | |
| Social Engineering / Awareness | [ ] Offen | ___.___._____ | |

### 2.3 Haftungsszenarien

| Szenario | Rechtsfolge |
|----------|-------------|
| Keine Risikomanagement-Massnahmen | Bussgeld bis 10 Mio. EUR oder 2% Jahresumsatz (wesentl. Einrichtungen) |
| Nicht-Registrierung beim BSI | Bussgeld bis 500.000 EUR |
| Verspaetete Vorfallmeldung | Bussgeld bis 10 Mio. EUR |
| Keine GF-Schulung | Persoenliche Haftung der Geschaeftsfuehrung |
| Unzureichende Supply-Chain-Sicherheit | Bussgeld + Schadensersatzansprueche |

---

## 3. Incident Reporting (ss 32 BSIG)

### 3.1 Meldefristen

```
Sicherheitsvorfall erkannt
         |
         v
   +-- 24 Stunden ---> Fruehwarnung an BSI
         |              (erste Einschaetzung, IoC falls vorhanden)
         |
         v
   +-- 72 Stunden ---> Detaillierte Vorfallmeldung
         |              (Schwere, Auswirkungen, IoC, Massnahmen)
         |
         v
   +-- 1 Monat ------> Abschlussbericht
                        (Ursachenanalyse, Massnahmen, Lessons Learned)
```

### 3.2 Fruehwarnung (24 Stunden)

**An:** BSI-Meldestelle (meldestelle@bsi.bund.de oder ueber BSI-Portal)

Folgende Informationen sind mindestens anzugeben:
- [ ] Datum und Uhrzeit der Entdeckung
- [ ] Erste Einschaetzung des Vorfalls
- [ ] Vermuteter Angriffsvektor
- [ ] Betroffene Systeme (z.B. OpMan_GPT)
- [ ] Grenzueberschreitende Auswirkungen (ja/nein)
- [ ] Indicators of Compromise (IoC), falls vorhanden

### 3.3 Detaillierte Vorfallmeldung (72 Stunden)

- [ ] Aktualisierung der Fruehwarnung
- [ ] Schweregrad-Einschaetzung
- [ ] Detaillierte Beschreibung der Auswirkungen
- [ ] Anzahl betroffener Personen / Systeme
- [ ] Ergriffene und geplante Gegenmassnahmen
- [ ] Technische Indikatoren (IoC, TTP nach MITRE ATT&CK)

### 3.4 Abschlussbericht (1 Monat)

- [ ] Vollstaendige Ursachenanalyse (Root Cause Analysis)
- [ ] Detaillierte Beschreibung aller Gegenmassnahmen
- [ ] Praventionsmassnahmen fuer die Zukunft
- [ ] Lessons Learned
- [ ] Aktualisierung des Risikomanagements

### 3.5 Wann ist ein Vorfall meldepflichtig?

Ein erheblicher Sicherheitsvorfall liegt vor, wenn:
- Schwerwiegende Betriebsstoerung der Dienste verursacht wird
- Finanzielle Verluste fuer die Einrichtung entstehen
- Erhebliche materielle oder immaterielle Schaeden fuer Dritte verursacht werden
- Die Einsatzfaehigkeit des Rettungsdienstes eingeschraenkt ist

---

## 4. Lieferkettensicherheit

### 4.1 Anforderungen an Lieferanten

- [ ] Sicherheitsanforderungen vertraglich festgelegt
- [ ] Recht auf Audits / Sicherheitsueberpruefungen vereinbart
- [ ] SLA fuer Sicherheitsupdates definiert
- [ ] Verpflichtung zur Meldung von Sicherheitsvorfaellen
- [ ] Subunternehmer-Regelung getroffen
- [ ] Exit-Strategie / Wechselmoeglichkeit definiert

### 4.2 Bewertungsmatrix Lieferanten

| Kriterium | Gewichtung | Bewertung (1-5) |
|-----------|-----------|----------------|
| ISO 27001 / SOC2 Zertifizierung | 20% | |
| Patch-Management SLA | 15% | |
| Incident Response Faehigkeit | 15% | |
| Datenschutz-Compliance | 15% | |
| Erreichbarkeit / Support | 10% | |
| Finanzielle Stabilitaet | 10% | |
| Subunternehmer-Transparenz | 10% | |
| Referenzen im KRITIS-Bereich | 5% | |

---

## 5. Bussgeldrahmen (Uebersicht)

### Wesentliche Einrichtungen (Rettungsdienst als Teil Gesundheitswesen)

| Verstoss | Bussgeld |
|----------|----------|
| Unzureichende Risikomanagement-Massnahmen | Bis 10 Mio. EUR oder 2% weltweiter Jahresumsatz |
| Verspaetete Vorfallmeldung | Bis 10 Mio. EUR oder 2% weltweiter Jahresumsatz |
| Nicht-Registrierung | Bis 500.000 EUR |
| Nicht-Kooperation mit BSI | Bis 2 Mio. EUR |
| Fehlende GF-Schulung | Persoenliche Haftung + Bussgeld |

### Wichtige Einrichtungen

| Verstoss | Bussgeld |
|----------|----------|
| Unzureichende Risikomanagement-Massnahmen | Bis 7 Mio. EUR oder 1,4% weltweiter Jahresumsatz |
| Verspaetete Vorfallmeldung | Bis 7 Mio. EUR oder 1,4% weltweiter Jahresumsatz |

---

## 6. Zeitplan / Meilensteine

| Meilenstein | Frist | Status |
|-------------|-------|--------|
| BSI-Registrierung | 06.03.2026 | [ ] Offen |
| Kontaktstelle benannt | 06.03.2026 | [ ] Offen |
| Risikoanalyse abgeschlossen | 30.04.2026 | [ ] Offen |
| ISMS aufgebaut (Grundschutz) | 30.06.2026 | [ ] Offen |
| Incident-Response-Plan getestet | 30.06.2026 | [ ] Offen |
| GF-Schulung durchgefuehrt | 30.06.2026 | [ ] Offen |
| Lieferantenbewertung abgeschlossen | 30.09.2026 | [ ] Offen |
| Erstes internes Audit | 31.12.2026 | [ ] Offen |
| Erster Penetrationstest | 31.12.2026 | [ ] Offen |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
