# Oesterreich-spezifische Anforderungen -- NISG 2026

**Dokument:** Oesterreichisches Netz- und Informationssystemsicherheitsgesetz 2026
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich
**Rechtsgrundlage:** NISG 2024 (BGBl. I Nr. 135/2024), NIS-2-RL (EU) 2022/2555

---

## 1. Einleitung

Dieses Dokument beschreibt die oesterreichspezifischen Anforderungen an den Betrieb der Einsatzleitsoftware OpMan_GPT im oesterreichischen Rechtsraum. Oesterreich hat die NIS-2-Richtlinie durch das novellierte Netz- und Informationssystemsicherheitsgesetz (NISG 2024) in nationales Recht umgesetzt.

Fuer Rettungsorganisationen in Oesterreich gelten neben dem NISG auch die jeweiligen Landesrettungsdienstgesetze.

---

## 2. Zustaendige Behoerden

| Behoerde | Zustaendigkeit | Kontakt |
|----------|---------------|---------|
| **Bundesamt fuer Cybersicherheit (BACYS)** | NIS2-Aufsicht, Registrierung, Meldestelle | cybersicherheit@bka.gv.at |
| **CERT.at** | Nationales CERT, technische Unterstuetzung | reports@cert.at |
| **Datenschutzbehoerde (DSB)** | DSGVO-Aufsicht | dsb@dsb.gv.at |
| **Landesregierung** | Rettungsdienstaufsicht (je Bundesland) | [Landesspezifisch] |

---

## 3. Registrierung beim Bundesamt fuer Cybersicherheit

### 3.1 Registrierungspflicht

Betreiber wesentlicher und wichtiger Einrichtungen muessen sich beim Bundesamt fuer Cybersicherheit (BACYS) im Bundeskanzleramt registrieren.

### 3.2 Registrierungsprozess

- [ ] **Schritt 1:** Pruefen, ob die Organisation als "wesentliche" oder "wichtige" Einrichtung gilt
  - Sektor: Gesundheitswesen (Anlage 1 NISG)
  - Teilsektor: Rettungsdienst / Notfalldienste
  - Schwellenwerte beachten (analog zu NIS-2-RL)

- [ ] **Schritt 2:** Online-Registrierung ueber das BACYS-Portal
  - Portal: https://nis.gv.at (oder ueber Unternehmensserviceportal USP)
  - Identifizierung mittels ID Austria (vormals Handysignatur)

- [ ] **Schritt 3:** Folgende Angaben bei der Registrierung:
  - Firmenname und Firmenbuchnummer
  - Sitz der Einrichtung
  - Sektor und Teilsektor
  - Kontaktdaten der Anlaufstelle (24/7)
  - IP-Adressbereiche
  - EU-Mitgliedstaaten, in denen Dienste erbracht werden

- [ ] **Schritt 4:** Bestaetigung abwarten und Registrierungsnummer archivieren

### 3.3 Meldepflichten (ss 19 NISG)

| Meldung | Frist | An |
|---------|-------|-----|
| Fruehwarnung | 24 Stunden | BACYS / CERT.at |
| Erstbewertung | 72 Stunden | BACYS |
| Zwischenbericht | Auf Anfrage | BACYS |
| Abschlussbericht | 1 Monat | BACYS |

---

## 4. Landesrettungsdienstgesetze

### 4.1 Uebersicht nach Bundeslaendern

Die Rettungsdienstgesetze der Bundeslaender regeln Organisation, Durchfuehrung und Dokumentation des Rettungsdienstes. OpMan_GPT muss die Anforderungen des jeweiligen Landesgesetzes erfuellen.

| Bundesland | Gesetz | Relevante Bestimmungen |
|-----------|--------|----------------------|
| **Burgenland** | Bgld. RettungsG 1995 | Dokumentationspflicht, Qualitaetssicherung |
| **Kaernten** | K-RDG 2003 | Leitstellenanforderungen, Einsatzdokumentation |
| **Niederoesterreich** | NOe RDG 2017 | Digitale Einsatzdokumentation, Datenschutz |
| **Oberoesterreich** | OOe RDG 1988 | Leitstellenbetrieb, Aufzeichnungspflichten |
| **Salzburg** | Sbg. RettG 2012 | Qualitaetsmanagement, Datensicherheit |
| **Steiermark** | Stmk. RettungsdienstG 2017 | IT-gestuetzte Dokumentation |
| **Tirol** | Tiroler RettG 2009 | Leitstellenbetrieb, Archivierung |
| **Vorarlberg** | Vlbg. RettG 2001 | Dokumentation, Aufbewahrungsfristen |
| **Wien** | Wr. RettungsG 2004 | Leitstellenanforderungen, Datenschutz |

### 4.2 Gemeinsame Anforderungen aller Landesgesetze

Die folgenden Anforderungen finden sich in allen Landesrettungsdienstgesetzen und muessen von OpMan_GPT erfuellt werden:

#### Einsatzdokumentation

- [ ] Vollstaendige Einsatzdokumentation (Zeitstempel, Massnahmen, Status)
- [ ] Unveraenderlichkeit der Dokumentation nach Abschluss (Audit-Trail)
- [ ] Aufbewahrungsfrist: Mindestens 10 Jahre (landesspezifisch bis 30 Jahre)
- [ ] Archivierung in lesbarem Format

#### Leitstellenanforderungen

- [ ] 24/7-Betrieb sichergestellt
- [ ] Redundante Kommunikationswege
- [ ] Protokollierung aller Funkgespraeche und Statusmeldungen
- [ ] Alarmierungsdokumentation (Zeitpunkt, Mittel, Empfaenger)

#### Datenschutz (AT-spezifisch)

- [ ] Patientendaten duerfen nur zum Zweck der Rettung verarbeitet werden
- [ ] Weitergabe nur an berechtigte Stellen (Spital, Polizei bei Pflicht)
- [ ] Loesch- bzw. Anonymisierungspflicht nach Ablauf der Aufbewahrungsfrist
- [ ] Auskunftsrecht der Betroffenen gemaess DSG/DSGVO

---

## 5. Oesterreichisches Datenschutzgesetz (DSG) -- Besonderheiten

### 5.1 Abweichungen zur DSGVO

| Thema | DSGVO | DSG (Oesterreich) |
|-------|-------|-------------------|
| Datenschutzbehoerde | Art. 51 ff. | Oesterreichische Datenschutzbehoerde (DSB) |
| Datenschutzbeauftragter | Art. 37 | Wie DSGVO, plus Meldung an DSB |
| Alter fuer Einwilligung | Art. 8: 16 Jahre (oder national ab 13) | 14 Jahre (ss 4 Abs. 4 DSG) |
| Videoüberwachung | Art. 6 | ss 12 DSG: Besondere Regelungen |
| Gesundheitsdaten | Art. 9 | ss 7 DSG: Zusaetzliche Schutzpflichten |
| Forschung | Art. 89 | ss 7 DSG: Erleichterte Verarbeitung |

### 5.2 Aufbewahrungsfristen in Oesterreich

| Datenart | Aufbewahrungsfrist | Rechtsgrundlage |
|----------|-------------------|-----------------|
| Einsatzdokumentation | 10-30 Jahre (landesabhaengig) | Landesrettungsdienstgesetz |
| Patientendaten | 10 Jahre (medizinisch) | GuKG, AerzteG |
| Funkprotokolle | 6 Monate bis 3 Jahre | TKG 2021 / Landesgesetz |
| Audit-Logs | Mindestens 3 Jahre | NISG, DSG |
| Rechnungsdaten | 7 Jahre | BAO (Bundesabgabenordnung) |
| Personalakten | 30 Jahre nach Ausscheiden | ArbeitnehmerInnenschutz |

---

## 6. Technische Anforderungen (NISG-spezifisch)

### 6.1 Mindestanforderungen fuer IT-Sicherheit

- [ ] Verschluesselung der Kommunikation (TLS 1.2+)
- [ ] Verschluesselung ruhender Daten (bei Gesundheitsdaten)
- [ ] Multi-Faktor-Authentifizierung fuer privilegierte Zugaenge
- [ ] Regelmaessige Sicherheitsupdates (kritisch: 72h)
- [ ] Protokollierung sicherheitsrelevanter Ereignisse
- [ ] Angriffserkennung (IDS/IPS)
- [ ] Backup-Konzept mit regelmaessigen Tests
- [ ] Incident-Response-Plan
- [ ] Krisenmanagement-Plan

### 6.2 Branchenspezifischer Sicherheitsstandard (B2S)

In Oesterreich koennen Sektoren branchenspezifische Sicherheitsstandards (B2S) beim BACYS einreichen. Fuer den Gesundheitssektor:

- [ ] Pruefen, ob ein B2S fuer den Rettungsdienst existiert
- [ ] Falls ja: Umsetzung des B2S dokumentieren
- [ ] Falls nein: ISO 27001 oder BSI IT-Grundschutz als Referenz nutzen

---

## 7. Zusammenarbeit mit oesterreichischen Behoerden

### 7.1 CERT.at -- Computer Emergency Response Team

- Anlaufstelle fuer technische Unterstuetzung bei Sicherheitsvorfaellen
- Bereitstellung von Warnmeldungen und Advisories
- Kontakt: reports@cert.at, +43 1 5056416 78

### 7.2 Zusammenarbeit Rettungsorganisationen

In Oesterreich sind die Rettungsorganisationen (Rotes Kreuz, Arbeiter-Samariter-Bund, Johanniter, Malteser, Rettungsdienst der Berufsfeuerwehren) haeufig landesweit organisiert. Die Koordination der IT-Sicherheit erfolgt idealerweise auf Bundesebene der jeweiligen Organisation.

### 7.3 Pruefungen durch BACYS

Das BACYS kann:
- Jederzeit Auskuenfte ueber die Einhaltung der Sicherheitsanforderungen verlangen
- Vor-Ort-Pruefungen durchfuehren (mit Ankuendigung)
- Bei erheblichen Vorfaellen anweisen, Massnahmen zu ergreifen
- Sanktionen verhaengen (Bussgelder bis zu 10 Mio. EUR)

---

## 8. Sanktionen in Oesterreich

| Verstoss | Bussgeld |
|----------|----------|
| Wesentliche Einrichtung: Unzureichende Sicherheitsmassnahmen | Bis 10 Mio. EUR oder 2% des weltweiten Jahresumsatzes |
| Wichtige Einrichtung: Unzureichende Sicherheitsmassnahmen | Bis 7 Mio. EUR oder 1,4% des weltweiten Jahresumsatzes |
| Nicht-Registrierung | Bis 500.000 EUR |
| Verspaetete Meldung eines Sicherheitsvorfalls | Bis 10 Mio. EUR |
| Nicht-Kooperation mit BACYS | Bis 2 Mio. EUR |

---

## 9. Checkliste Oesterreich-spezifisch

- [ ] Registrierung beim BACYS abgeschlossen
- [ ] ID Austria fuer vertretungsberechtigte Person vorhanden
- [ ] Anlaufstelle (24/7) benannt und gemeldet
- [ ] Relevantes Landesrettungsdienstgesetz identifiziert
- [ ] Aufbewahrungsfristen gemaess Landesgesetz eingehalten
- [ ] Datenschutzbehoerde (DSB) als zustaendige Aufsicht beruecksichtigt
- [ ] DSG-Besonderheiten (ss 4 Abs. 4, ss 7, ss 12) implementiert
- [ ] CERT.at als technische Anlaufstelle eingetragen
- [ ] Branchenspezifischer Sicherheitsstandard (B2S) geprueft
- [ ] Zusammenarbeit mit Dachorganisation der Rettungsorganisation koordiniert

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
