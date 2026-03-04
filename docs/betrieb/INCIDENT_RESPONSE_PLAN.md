# Incident Response Plan

**Dokument:** Incident Response Plan (Vorfallsreaktionsplan)
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich

---

## 1. Zweck und Geltungsbereich

Dieser Plan regelt die Erkennung, Bewertung, Reaktion und Nachbereitung von IT-Sicherheitsvorfaellen im Zusammenhang mit dem Betrieb von OpMan_GPT. Er gilt fuer alle Personen, die am Betrieb, der Wartung oder der Nutzung des Systems beteiligt sind.

---

## 2. Eskalationsstufen

### Stufe 1: Ereignis (Event)

**Beschreibung:** Auffaelligkeit, die noch keine bestaetigte Sicherheitsverletzung darstellt.

| Aspekt | Details |
|--------|---------|
| **Beispiele** | Vereinzelte fehlgeschlagene Logins, ungewoehnliche Log-Eintraege, Anomalie-Warnung in OpMan_GPT |
| **Bewertung** | Durch IT-Betrieb / On-Call |
| **Reaktionszeit** | Naechster Arbeitstag |
| **Massnahmen** | Analyse, Dokumentation, ggf. Eskalation |
| **Meldepflicht** | Keine |

### Stufe 2: Sicherheitsvorfall (Incident)

**Beschreibung:** Bestaetigte Verletzung der Vertraulichkeit, Integritaet oder Verfuegbarkeit.

| Aspekt | Details |
|--------|---------|
| **Beispiele** | Erfolgreicher unbefugter Zugriff, Datenverlust, Malware-Befall, DDoS-Angriff |
| **Bewertung** | IT-Sicherheitsbeauftragter |
| **Reaktionszeit** | 4 Stunden |
| **Massnahmen** | Eindaemmung, Analyse, Wiederherstellung |
| **Meldepflicht** | Intern: GF, DSB; ggf. BSI (24h Fruehwarnung) |

### Stufe 3: Schwerer Sicherheitsvorfall (Major Incident)

**Beschreibung:** Sicherheitsvorfall mit erheblichen Auswirkungen auf den Betrieb oder betroffene Personen.

| Aspekt | Details |
|--------|---------|
| **Beispiele** | Kompromittierung von Gesundheitsdaten, Ransomware, vollstaendiger Systemausfall, Datenleck |
| **Bewertung** | IS-Beauftragter + Geschaeftsfuehrung |
| **Reaktionszeit** | 1 Stunde |
| **Massnahmen** | Sofortige Eindaemmung, Krisenstab, Forensik, Notbetrieb |
| **Meldepflicht** | BSI (24h), Aufsichtsbehoerde (72h), ggf. Betroffene |

### Stufe 4: Krise (Crisis)

**Beschreibung:** Existenzbedrohender Vorfall oder Vorfall mit Gefaehrdung von Menschenleben.

| Aspekt | Details |
|--------|---------|
| **Beispiele** | Ausfall der Einsatzleitsoftware bei laufenden Rettungseinsaetzen, gezielter Angriff auf KRITIS-Infrastruktur |
| **Bewertung** | Geschaeftsfuehrung + externer Krisenberater |
| **Reaktionszeit** | Sofort |
| **Massnahmen** | Sofortige Umschaltung auf Notbetrieb, Krisenkommunikation, Strafanzeige |
| **Meldepflicht** | BSI (sofort), Polizei/StA, Aufsichtsbehoerde, Betroffene, ggf. Oeffentlichkeit |

---

## 3. Kontaktliste

### 3.1 Internes Incident Response Team

| Rolle | Name | Telefon | E-Mail | Erreichbarkeit |
|-------|------|---------|--------|---------------|
| Incident Manager | [Name] | [Tel] | [E-Mail] | 24/7 |
| IT-Sicherheitsbeauftragter | [Name] | [Tel] | [E-Mail] | 24/7 |
| Stellvertreter ISB | [Name] | [Tel] | [E-Mail] | 24/7 |
| IT-Administration | [Name] | [Tel] | [E-Mail] | 24/7 |
| Datenschutzbeauftragter | [Name] | [Tel] | [E-Mail] | Geschaeftszeiten |
| Geschaeftsfuehrung | [Name] | [Tel] | [E-Mail] | 24/7 (Eskalation) |
| Pressesprecher | [Name] | [Tel] | [E-Mail] | Geschaeftszeiten |

### 3.2 Externe Kontakte

| Organisation | Zweck | Telefon | E-Mail |
|-------------|-------|---------|--------|
| BSI Meldestelle | NIS2-Vorfallmeldung | +49 228 99 9582-5666 | meldestelle@bsi.bund.de |
| BSI CERT-Bund | Technische Hilfe | +49 228 99 9582-222 | certbund@bsi.bund.de |
| CERT.at (Oesterreich) | Technische Hilfe (AT) | +43 1 5056416-78 | reports@cert.at |
| Landesdatenschutzbehoerde | Datenpannen-Meldung | [Tel] | [E-Mail] |
| Polizei Cybercrime | Strafanzeige | [110 / Landeskriminalamt] | |
| Forensik-Dienstleister | Forensische Analyse | [Tel] | [E-Mail] |
| Rechtsanwalt (IT-Recht) | Rechtliche Beratung | [Tel] | [E-Mail] |
| Cyberversicherung | Schadenmeldung | [Tel] | [Policennummer] |

---

## 4. Incident Response Prozess

### Phase 1: Erkennung und Meldung

1. **Automatische Erkennung** durch OpMan_GPT:
   - Anomalie-Erkennung (neue IP, Geschaeftszeiten, Fehlversuche)
   - Breach-Erkennung (Massenexporte, unaut. Zugriffe)
   - Account-Sperrung (Brute-Force)
   - Monitoring (/health, /metrics)

2. **Manuelle Erkennung** durch:
   - Mitarbeiter-Meldung
   - Externe Hinweise (BSI-Warnung, CERT)
   - Routine-Pruefung der Audit-Logs

3. **Meldung** an Incident Manager:
   - Was ist passiert?
   - Wann wurde es entdeckt?
   - Welche Systeme sind betroffen?
   - Erste Einschaetzung der Schwere

### Phase 2: Bewertung und Klassifizierung

1. Eskalationsstufe bestimmen (1-4)
2. Betroffene Daten und Systeme identifizieren
3. Auswirkungen auf Rettungsdienst bewerten
4. Meldepflichten pruefen (BSI, Datenschutz)
5. Incident Response Team zusammenrufen (ab Stufe 2)

### Phase 3: Eindaemmung (Containment)

**Kurzfristig (Stunden):**
- Betroffene Accounts sperren
- Betroffene Netzwerksegmente isolieren
- Schadsoftware-Verbreitung stoppen
- Beweismittel sichern (Logs, Festplattenimages)
- Zugriffswege schliessen

**Langfristig (Tage):**
- Kompromittierte Systeme identifizieren und isolieren
- Backdoors suchen und entfernen
- Passwoerter zuruecksetzen (alle betroffenen Accounts)
- Verschluesselungsschluessel rotieren (falls kompromittiert)
- Temporaere Sicherheitsmassnahmen implementieren

### Phase 4: Beseitigung (Eradication)

1. Ursache des Vorfalls identifizieren (Root Cause Analysis)
2. Schadsoftware vollstaendig entfernen
3. Schwachstellen patchen
4. Systeme von sauberen Backups wiederherstellen (falls noetig)
5. Konfigurationen ueberpruefen und haerten

### Phase 5: Wiederherstellung (Recovery)

1. Systeme schrittweise wieder in Betrieb nehmen
2. Integritaetspruefung der Datenbank
3. Audit-Log-Integritaet verifizieren (Hash-Chain)
4. Funktionalitaet verifizieren (Smoke Tests)
5. Monitoring verstaerken (erhoehte Aufmerksamkeit)
6. Benutzer informieren

### Phase 6: Nachbereitung (Lessons Learned)

1. Post-Incident-Review durchfuehren (innerhalb von 2 Wochen)
2. Timeline des Vorfalls erstellen
3. Was hat gut funktioniert? Was muss verbessert werden?
4. Massnahmen zur Verhinderung aehnlicher Vorfaelle ableiten
5. Incident Response Plan aktualisieren
6. Schulungen anpassen
7. Abschlussbericht erstellen

---

## 5. Kommunikationsvorlagen

### 5.1 Interne Erstmeldung

```
SICHERHEITSVORFALL - INTERNE MELDUNG
=====================================
Datum/Uhrzeit: ___.___.______ __:__
Melder: ___________________________
Eskalationsstufe: [ ] 1 [ ] 2 [ ] 3 [ ] 4

BESCHREIBUNG:
_____________________________________________________________

BETROFFENE SYSTEME:
[ ] OpMan_GPT (Einsatzleitsoftware)
[ ] Datenbankserver
[ ] Netzwerkinfrastruktur
[ ] Sonstige: _________________

SOFORTMASSNAHMEN ERGRIFFEN:
_____________________________________________________________

NAECHSTE SCHRITTE:
_____________________________________________________________
```

### 5.2 BSI-Fruehwarnung (24 Stunden)

```
An: meldestelle@bsi.bund.de
Betreff: NIS2 Fruehwarnung - [Organisation] - [Kurzbeschreibung]

FRUEHWARNUNG gemaess ss 32 Abs. 1 BSIG

Registrierungsnummer: [BSI-Reg-Nr.]
Einrichtung: [Organisation]
Sektor: Gesundheitswesen / Rettungsdienst

Datum/Uhrzeit der Entdeckung: ___.___.______ __:__

Erste Einschaetzung:
_____________________________________________________________

Betroffene Dienste:
[ ] Einsatzleitsystem (OpMan_GPT)
[ ] Kommunikationssysteme
[ ] Sonstige: _________________

Grenzueberschreitende Auswirkungen: [ ] Ja [ ] Nein

Indicators of Compromise (soweit bekannt):
_____________________________________________________________

Kontakt fuer Rueckfragen:
Name: _________________________
Telefon: ______________________
E-Mail: _______________________

Dies ist eine Fruehwarnung. Eine detaillierte Meldung folgt
innerhalb von 72 Stunden.
```

### 5.3 Statusupdate-Template

```
INCIDENT UPDATE #___
====================
Datum/Uhrzeit: ___.___.______ __:__
Incident-ID: INC-________
Status: [ ] Aktiv [ ] Eingedaemmt [ ] Behoben [ ] Abgeschlossen

AKTUELLER STAND:
_____________________________________________________________

NEUE ERKENNTNISSE:
_____________________________________________________________

MASSNAHMEN SEIT LETZTEM UPDATE:
_____________________________________________________________

NAECHSTE SCHRITTE:
_____________________________________________________________

NAECHSTES UPDATE: ___.___.______ __:__ Uhr
```

---

## 6. Notbetrieb bei Ausfall von OpMan_GPT

Bei einem vollstaendigen Ausfall von OpMan_GPT muessen Rettungseinsaetze auf alternative Verfahren umgestellt werden:

| Funktion | Notverfahren |
|----------|-------------|
| Einsatzkoordination | Papierbasierte Disposition (Vordrucke bereithalten) |
| Funkstatus | Manuelle Statuserfassung auf Whiteboard |
| GPS-Tracking | Entfaellt; Standortmeldung per Funk |
| Falldokumentation | Papierbasierte Einsatzprotokolle |
| Alarmierung | Telefon / Funk direkt |
| Kommunikation | Analogfunk als Fallback |

**Voraussetzungen fuer Notbetrieb:**
- [ ] Papiervordrucke fuer Einsatzprotokolle vorhalten
- [ ] Whiteboard mit Magnetkarten fuer Disposition
- [ ] Analogfunk-Geraete betriebsbereit
- [ ] Telefonliste aller Einsatzkraefte aktuell
- [ ] Personal in Notverfahren geschult

---

## 7. Uebungsplan

| Uebung | Turnus | Teilnehmer | Dauer |
|--------|--------|-----------|-------|
| Tabletop-Uebung (Planspiel) | Halbjaehrlich | IR-Team, GF | 2h |
| Technische Uebung (Simulation) | Jaehrlich | IT-Team | 4h |
| Vollstaendige Uebung | Jaehrlich | Alle Beteiligten | 1 Tag |
| Notbetrieb-Uebung | Halbjaehrlich | Leitstellenpersonal | 2h |
| Breach-Notification-Uebung | Jaehrlich | DSB, ISB, GF | 2h |

---

## 8. Anhang: Incident-Log Vorlage

| Zeitpunkt | Aktion | Durchgefuehrt von | Ergebnis |
|-----------|--------|-------------------|----------|
| ___.___ __:__ | | | |
| ___.___ __:__ | | | |
| ___.___ __:__ | | | |
| ___.___ __:__ | | | |
| ___.___ __:__ | | | |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
