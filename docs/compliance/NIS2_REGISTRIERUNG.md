# NIS2-Registrierung beim BSI

**Dokument:** NIS2-Registrierungsleitfaden
**System:** OpMan-GPT -- Einsatzleitsoftware
**Version:** 1.0
**Stand:** 04.03.2026
**Klassifikation:** VERTRAULICH
**Frist:** 06.03.2026

---

## 1. Einleitung

Die NIS2-Richtlinie (EU 2022/2555) wurde in deutsches Recht durch das NIS2-Umsetzungsgesetz (NIS2UmsuCG) uebergefuehrt. Betreiber von Einsatzleitsystemen im Rettungsdienst fallen als Einrichtungen des Gesundheitssektors bzw. der oeffentlichen Verwaltung unter die Kategorie "wesentliche Einrichtungen" (essential entities) gemaess Anhang I der Richtlinie.

Die Registrierung beim Bundesamt fuer Sicherheit in der Informationstechnik (BSI) ist **bis zum 06.03.2026** verpflichtend durchzufuehren.

---

## 2. Schritt-fuer-Schritt Registrierungsprozess

### Schritt 1: Betroffenheitspruefung

- [ ] Pruefen, ob die Einrichtung unter NIS2 faellt (Sektorzugehoerigkeit: Gesundheitswesen)
- [ ] Feststellen der Kategorie: **Wesentliche Einrichtung** (essential) oder **Wichtige Einrichtung** (important)
- [ ] Rettungsdienst / Notfalldienste: In der Regel "wesentliche Einrichtung"
- [ ] Schwellenwerte pruefen: > 50 Mitarbeiter ODER > 10 Mio. EUR Jahresumsatz
- [ ] Sonderfall: Unabhaengig von Groesse, wenn Einsatzleitsoftware als kritische Infrastruktur eingestuft

### Schritt 2: BSI-Portal-Zugang

1. Aufruf des BSI-Registrierungsportals: `https://nis2-registrierung.bsi.bund.de`
2. Organisationskonto anlegen (Verantwortlicher der Geschaeftsfuehrung)
3. ELSTER-Zertifikat oder eID zur Authentifizierung verwenden
4. Zugangsbestaetigung per Post abwarten (ca. 3-5 Werktage)

### Schritt 3: Stammdaten erfassen

Folgende Informationen im Portal eintragen:

| Feld | Beschreibung | Beispiel |
|------|-------------|----------|
| Name der Einrichtung | Offizieller Name | [Organisation] |
| Rechtsform | z.B. e.V., gGmbH, KdoeR | [Rechtsform] |
| Handelsregisternummer | HR-Nummer oder aehnlich | [HR-Nummer] |
| Anschrift | Hauptsitz | [Adresse] |
| Sektor | NIS2-Sektor | Gesundheitswesen |
| Teilsektor | NIS2-Teilsektor | Rettungsdienste / Notfalldienste |
| Kategorie | Wesentlich/Wichtig | Wesentliche Einrichtung |
| Mitarbeiterzahl | Gesamtanzahl | [Anzahl] |
| Jahresumsatz | Letztes Geschaeftsjahr | [Betrag] EUR |

### Schritt 4: Kontaktstelle benennen

- [ ] Hauptansprechpartner (Kontaktstelle) festlegen
- [ ] Stellvertretende Kontaktstelle benennen
- [ ] 24/7-Erreichbarkeit sicherstellen (fuer Vorfallsmeldungen)
- [ ] Kontaktstelle dem BSI melden

### Schritt 5: IT-Systeme registrieren

- [ ] OpMan-GPT als Einsatzleitsystem registrieren
- [ ] Abhaengige Systeme erfassen (Datenbank, Netzwerk, Kommunikation)
- [ ] Standorte der IT-Systeme angeben
- [ ] Betriebsverantwortliche benennen

### Schritt 6: Registrierung abschliessen

- [ ] Alle Pflichtfelder pruefen
- [ ] Registrierung durch Geschaeftsfuehrung freigeben lassen
- [ ] Registrierung absenden
- [ ] Bestaetigungsnummer archivieren

---

## 3. Erforderliche Informationen -- Checkliste

### 3.1 Organisationsdaten

- [ ] Vollstaendiger Name der Einrichtung
- [ ] Anschrift (Strasse, PLZ, Ort)
- [ ] Rechtsform
- [ ] Handelsregisternummer / Vereinsregisternummer
- [ ] Umsatzsteuer-ID
- [ ] Branche / Sektor nach NIS2-Klassifikation
- [ ] Anzahl der Mitarbeiter
- [ ] Jahresumsatz / Jahresbilanzsumme

### 3.2 Kontaktdaten

- [ ] Name des Geschaeftsfuehrers / Vorstands
- [ ] E-Mail-Adresse (dedizierte NIS2-Mailbox empfohlen)
- [ ] Telefonnummer (24/7 erreichbar)
- [ ] Mobilnummer fuer Notfaelle
- [ ] Stellvertreter mit allen Kontaktdaten

### 3.3 Technische Angaben

- [ ] Beschreibung der kritischen Dienste
- [ ] Anzahl und Art der IT-Systeme
- [ ] Eingesetzte Einsatzleitsoftware (OpMan-GPT)
- [ ] Netzwerkarchitektur (ueberblick)
- [ ] Vorhandene Sicherheitsmassnahmen
- [ ] Vorhandene Zertifizierungen (ISO 27001, BSI-Grundschutz)

### 3.4 Vorfallsmeldeverfahren

- [ ] Interner Prozess fuer Vorfallserkennung
- [ ] Meldekette (intern -> BSI)
- [ ] Kontaktdaten des CERT/CSIRT

---

## 4. Kontaktstelle -- Benennungsvorlage

```
BENENNUNG DER KONTAKTSTELLE GEMAESS NIS2UMSUCG

Einrichtung:      [Name der Organisation]
Registrierungs-Nr: [wird vom BSI vergeben]
Datum:             [Datum]

HAUPTKONTAKTSTELLE:
Name:              [Vor- und Nachname]
Funktion:          [z.B. IT-Sicherheitsbeauftragter / CISO]
E-Mail:            [nis2@organisation.de]
Telefon:           [+49 ...]
Mobil:             [+49 ...]
Erreichbarkeit:    24/7

STELLVERTRETENDE KONTAKTSTELLE:
Name:              [Vor- und Nachname]
Funktion:          [z.B. Stellv. IT-Sicherheitsbeauftragter]
E-Mail:            [nis2-stellv@organisation.de]
Telefon:           [+49 ...]
Mobil:             [+49 ...]
Erreichbarkeit:    24/7

ESKALATIONSKONTAKT (GESCHAEFTSFUEHRUNG):
Name:              [Vor- und Nachname]
Funktion:          [Geschaeftsfuehrer / Vorstand]
E-Mail:            [gf@organisation.de]
Telefon:           [+49 ...]

Die benannten Kontaktstellen sind berechtigt, im Namen der Einrichtung
Vorfallsmeldungen an das BSI zu uebermitteln und Kommunikation
mit dem BSI durchzufuehren.

Unterschrift Geschaeftsfuehrung:    ________________________

Datum:                               ________________________
```

---

## 5. Fristen und Pflichten nach Registrierung

| Pflicht | Frist | Beschreibung |
|---------|-------|-------------|
| Registrierung | **06.03.2026** | Erstregistrierung beim BSI |
| Aenderungsmeldung | 14 Tage | Bei Aenderung der Stammdaten oder Kontaktstellen |
| Vorfallsmeldung (Fruehwarnung) | 24 Stunden | Nach Erkennung eines erheblichen Sicherheitsvorfalls |
| Vorfallsmeldung (Bericht) | 72 Stunden | Detaillierter Bericht mit Bewertung |
| Abschlussbericht | 1 Monat | Nach Abschluss der Vorfallsbehandlung |
| Sicherheitsmassnahmen | Laufend | Implementierung und Aufrechterhaltung |
| Nachweispruefung | Alle 2 Jahre | Nachweis der Sicherheitsmassnahmen |

---

## 6. Wichtige Hinweise

### 6.1 Sanktionen bei Nichtregistrierung

- Bussgelder bis zu **10 Mio. EUR** oder **2% des weltweiten Jahresumsatzes** (wesentliche Einrichtungen)
- Persoenliche Haftung der Geschaeftsfuehrung
- Anordnungsbefugnisse des BSI

### 6.2 Dokumentationsanforderungen

Alle Registrierungsunterlagen und die Kommunikation mit dem BSI sind mindestens **5 Jahre** aufzubewahren. Die folgenden Dokumente muessen vorgehalten werden:

- Registrierungsbestaetigung
- Korrespondenz mit dem BSI
- Nachweis der benannten Kontaktstellen
- Dokumentation der Sicherheitsmassnahmen
- Vorfallsberichte und Meldungen

### 6.3 Zusammenwirken mit Landesbehoerden

In foederalen Strukturen (z.B. Bayern) ist zusaetzlich die Abstimmung mit dem Landesamt fuer Sicherheit in der Informationstechnik (LSI Bayern) erforderlich. Rettungsdiensttraeger, die unter das BayRDG fallen, muessen ggf. zusaetzliche landesrechtliche Meldepflichten beachten.

---

## 7. Ansprechpartner BSI

| Kontakt | Details |
|---------|---------|
| BSI-Registrierungsportal | https://nis2-registrierung.bsi.bund.de |
| BSI-Hotline NIS2 | +49 228 99 9582-5500 |
| E-Mail | nis2@bsi.bund.de |
| Lagezentrum (24/7) | +49 228 99 9582-0 |
| Postanschrift | BSI, Godesberger Allee 185-189, 53175 Bonn |

---

*Dieses Dokument ist Teil der Compliance-Dokumentation fuer OpMan-GPT und unterliegt der regelmaessigen Ueberpruefung.*
