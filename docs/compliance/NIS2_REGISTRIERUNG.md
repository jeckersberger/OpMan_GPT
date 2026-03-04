# NIS2-Registrierung beim BSI

**Dokument:** NIS2-Registrierungsleitfaden
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich
**Frist:** 06.03.2026 (Registrierungspflicht)

---

## 1. Einleitung

Gemaess dem NIS-2-Umsetzungs- und Cybersicherheitsstaerkungsgesetz (NIS2UmsuCG) sind Betreiber wesentlicher und wichtiger Einrichtungen verpflichtet, sich beim Bundesamt fuer Sicherheit in der Informationstechnik (BSI) zu registrieren. Rettungsdienste und Leitstellen fallen als Teil des Sektors "Gesundheitswesen" unter die Kategorie der wesentlichen Einrichtungen.

**Rechtsgrundlage:** ss 33 BSIG (neu), Art. 3 NIS-2-Richtlinie (EU) 2022/2555

**ACHTUNG: Die Registrierungsfrist endet am 06.03.2026. Die Registrierung muss unverzueglich erfolgen.**

---

## 2. Schritt-fuer-Schritt Registrierungsprozess

### Schritt 1: Einrichtungstyp bestimmen

- [ ] Pruefen, ob die Organisation als "wesentliche Einrichtung" (essential entity) oder "wichtige Einrichtung" (important entity) gilt
- [ ] Sektor: **Gesundheitswesen** (Anhang I Nr. 5 NIS-2-RL)
- [ ] Teilsektor: Rettungsdienst / Notfalldienste
- [ ] Schwellenwerte pruefen:
  - Mitarbeiterzahl >= 50 ODER
  - Jahresumsatz > 10 Mio. EUR ODER
  - Jahresbilanzsumme > 10 Mio. EUR
  - ODER: Sonderregelung fuer kritische Infrastrukturen unabhaengig von Groesse

### Schritt 2: BSI-Portal aufrufen

- [ ] Registrierungsportal: **https://nis2-registrierung.bsi.bund.de**
- [ ] Organisationskonto anlegen (ELSTER-Zertifikat oder eID erforderlich)
- [ ] Verantwortliche Person mit Vertretungsbefugnis benennen

### Schritt 3: Stammdaten erfassen

Folgende Informationen werden bei der Registrierung benoetigt:

| Feld | Beschreibung | Beispiel |
|------|-------------|----------|
| Name der Einrichtung | Vollstaendiger rechtlicher Name | [Organisation] |
| Rechtsform | z.B. e.V., gGmbH, KdoeR | [Rechtsform] |
| Anschrift | Sitz der Einrichtung | [Strasse, PLZ, Ort] |
| Sektor | Zugeordneter NIS2-Sektor | Gesundheitswesen |
| Teilsektor | Spezifischer Teilsektor | Rettungsdienst / Leitstelle |
| Registernummer | Handelsregister / Vereinsregister | [HRB/VR-Nummer] |
| Umsatzsteuer-ID | Falls vorhanden | [USt-IdNr.] |
| Mitarbeiterzahl | Anzahl Beschaeftigte | [Anzahl] |
| Jahresumsatz | Letztes Geschaeftsjahr | [Betrag EUR] |
| EU-Mitgliedstaaten | Staaten, in denen Dienste erbracht werden | Deutschland [, Oesterreich] |
| IP-Adressbereiche | Oeffentliche IP-Bereiche der Einrichtung | [CIDR-Notation] |

### Schritt 4: Kontaktstelle benennen

- [ ] Primaere Kontaktstelle (24/7 erreichbar) benennen
- [ ] Stellvertretende Kontaktstelle benennen
- [ ] Kontaktdaten in BSI-Portal eintragen

### Schritt 5: IT-Systeme und Dienste melden

- [ ] Kritische IT-Systeme auflisten (inkl. OpMan_GPT)
- [ ] Netzwerk-Infrastruktur beschreiben
- [ ] Abhaengigkeiten zu Drittanbietern dokumentieren
- [ ] Einsatzgebiet und Versorgungsbereich angeben

### Schritt 6: Registrierung abschliessen

- [ ] Angaben auf Vollstaendigkeit pruefen
- [ ] Registrierung durch vertretungsberechtigte Person bestaetigen
- [ ] Bestaetigungsmail archivieren
- [ ] BSI-Registrierungsnummer notieren: ________________

---

## 3. Kontaktstellen-Template

### Primaere Kontaktstelle (gemeldete Kontaktstelle gem. ss 33 Abs. 2 BSIG)

| Feld | Angabe |
|------|--------|
| **Name** | [Vorname Nachname] |
| **Funktion** | [z.B. IT-Sicherheitsbeauftragter, CISO] |
| **Telefon (24/7)** | [+49 xxx xxxxxxx] |
| **Mobiltelefon** | [+49 xxx xxxxxxx] |
| **E-Mail** | [name@organisation.de] |
| **PGP-Fingerprint** | [Falls vorhanden] |
| **Erreichbarkeit** | 24/7 (Bereitschaftsregelung) |

### Stellvertretende Kontaktstelle

| Feld | Angabe |
|------|--------|
| **Name** | [Vorname Nachname] |
| **Funktion** | [z.B. Stellv. IT-Leiter] |
| **Telefon (24/7)** | [+49 xxx xxxxxxx] |
| **Mobiltelefon** | [+49 xxx xxxxxxx] |
| **E-Mail** | [name@organisation.de] |
| **Erreichbarkeit** | 24/7 (Bereitschaftsregelung) |

### Eskalationskontakt Geschaeftsfuehrung

| Feld | Angabe |
|------|--------|
| **Name** | [Vorname Nachname] |
| **Funktion** | [Geschaeftsfuehrer / Vorstand] |
| **Telefon** | [+49 xxx xxxxxxx] |
| **E-Mail** | [name@organisation.de] |

---

## 4. Checkliste erforderliche Unterlagen

- [ ] Handelsregisterauszug / Vereinsregisterauszug (nicht aelter als 6 Monate)
- [ ] Organisationsstruktur / Organigramm
- [ ] Uebersicht der erbrachten Dienste im Bereich Rettungsdienst
- [ ] Netzplan / IT-Infrastruktur-Uebersicht
- [ ] ISMS-Dokumentation (falls vorhanden)
- [ ] Benennung des IT-Sicherheitsbeauftragten
- [ ] Nachweis ueber Cyberversicherung (falls vorhanden)
- [ ] Letzte Sicherheitsaudit-Berichte (falls vorhanden)
- [ ] Uebersicht ueber eingesetzte IT-Systeme (inkl. OpMan_GPT)
- [ ] Notfallkontaktliste (24/7)
- [ ] Datenschutzbeauftragter (Kontaktdaten)

---

## 5. Fristen und Pflichten nach Registrierung

| Pflicht | Frist | Rechtsgrundlage |
|---------|-------|-----------------|
| Registrierung | **06.03.2026** | ss 33 BSIG |
| Erstmeldung Sicherheitsvorfall | 24 Stunden (Fruehwarnung) | ss 32 Abs. 1 BSIG |
| Detaillierte Vorfallmeldung | 72 Stunden | ss 32 Abs. 2 BSIG |
| Abschlussbericht Vorfall | 1 Monat | ss 32 Abs. 4 BSIG |
| Risikomanagement-Massnahmen | Laufend | ss 30 BSIG |
| Geschaeftsfuehrer-Schulung | Regelmaessig | ss 38 BSIG |
| Sicherheitsaudit | Alle 2 Jahre | ss 39 BSIG |

---

## 6. Aenderungsmeldungen

Aenderungen an den registrierten Angaben muessen dem BSI **unverzueglich, spaetestens innerhalb von 2 Wochen** gemeldet werden. Dies betrifft insbesondere:

- Aenderung der Kontaktstelle
- Aenderung der Anschrift / Rechtsform
- Aenderung des Leistungsspektrums
- Wesentliche Aenderungen an IT-Systemen
- Aenderung der IP-Adressbereiche

---

## 7. Sanktionen bei Nicht-Registrierung

| Verstoss | Bussgeld |
|----------|----------|
| Unterlassene Registrierung | Bis zu 500.000 EUR |
| Falsche / unvollstaendige Angaben | Bis zu 500.000 EUR |
| Unterlassene Aenderungsmeldung | Bis zu 100.000 EUR |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
