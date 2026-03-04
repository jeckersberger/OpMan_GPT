# Datenpannen-Meldeverfahren (Breach Notification)

**Dokument:** Meldeverfahren bei Datenschutzverletzungen gemaess Art. 33, 34 DSGVO
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich

---

## 1. Geltungsbereich

Dieses Verfahren gilt fuer alle Verletzungen des Schutzes personenbezogener Daten im Zusammenhang mit OpMan_GPT. Es regelt die interne Meldekette, die Bewertung, die Meldung an die Aufsichtsbehoerde und die Benachrichtigung betroffener Personen.

---

## 2. Definition Datenschutzverletzung

Eine Verletzung des Schutzes personenbezogener Daten liegt vor bei einer Verletzung der Sicherheit, die zur:
- **Vernichtung** (Daten unwiederbringlich verloren)
- **Veraenderung** (Daten manipuliert)
- **unbefugten Offenlegung** (Daten unberechtigt zugaenglich)
- **unbefugtem Zugang** (unbefugte Person hat Zugriff erlangt)

von personenbezogenen Daten fuehrt (Art. 4 Nr. 12 DSGVO).

---

## 3. Interne Meldekette

```
Entdeckung der Datenpanne
         |
         v
    Mitarbeiter / System
    (Breach-Erkennung in OpMan_GPT)
         |
         v (sofort)
    IT-Sicherheitsbeauftragter
         |
         v (innerhalb 4 Stunden)
    Datenschutzbeauftragter
         |
         v (Bewertung)
    +-----------------+------------------+
    |                                    |
    v                                    v
Kein Risiko fuer                   Risiko fuer Betroffene
Betroffene                              |
    |                           +--------+--------+
    v                           |                 |
Dokumentation              Meldung an         Hohes Risiko?
(nur intern)               Aufsichtsbehoerde       |
                           (72 Stunden)        +---+---+
                                |              |       |
                                v              v       v
                           Abschlussbericht  Benachrichtigung
                           (wenn Risiko)     betroffener Personen
                                             (unverzueglich)
```

---

## 4. Sofort-Checkliste bei Entdeckung einer Datenpanne

- [ ] **Zeitpunkt** der Entdeckung dokumentieren: ___.___.______ __:__ Uhr
- [ ] **Entdecker** dokumentieren: Name, Funktion
- [ ] **Art der Panne** beschreiben (was ist passiert?)
- [ ] **Betroffene Systeme** identifizieren
- [ ] IT-Sicherheitsbeauftragten informieren
- [ ] Sofortmassnahmen ergreifen (Zugang sperren, System isolieren)
- [ ] Beweise sichern (Screenshots, Logs, Festplattenimages)
- [ ] Datenschutzbeauftragten informieren
- [ ] 72-Stunden-Frist beginnt ab Kenntniserlangung

---

## 5. Risikobewertung

### 5.1 Bewertungskriterien

| Kriterium | Niedrig (1) | Mittel (2) | Hoch (3) | Sehr hoch (4) |
|-----------|-------------|-----------|----------|---------------|
| Datenkategorie | Pseudonyme | Kontaktdaten | Login-Daten | Gesundheitsdaten |
| Anzahl Betroffene | < 10 | 10 - 100 | 100 - 1.000 | > 1.000 |
| Reversibilitaet | Vollstaendig | Weitgehend | Teilweise | Nicht moeglich |
| Schadensart | Unannehmlichkeit | Diskriminierung | Finanzieller Schaden | Gesundheitsgefaehrdung |
| Identifizierbarkeit | Nicht moeglich | Schwierig | Moeglich | Unmittelbar |

### 5.2 Bewertungsmatrix

| Gesamtbewertung | Massnahme |
|-----------------|-----------|
| 1-5 Punkte | Nur interne Dokumentation |
| 6-10 Punkte | Meldung an Aufsichtsbehoerde (Art. 33) |
| 11-16 Punkte | Meldung + Benachrichtigung Betroffener (Art. 33 + 34) |
| 17-20 Punkte | Sofortmeldung + Benachrichtigung + Strafanzeige pruefen |

### 5.3 Besondere Bewertung fuer OpMan_GPT

Bei Datenpannen in OpMan_GPT ist zu beachten:
- **Gesundheitsdaten (Art. 9):** Automatisch hohes Risiko
- **Rettungseinsatzdaten:** Koennten Rueckschluesse auf Gesundheitszustand erlauben
- **GPS-Standortdaten:** Ermoeglichen Bewegungsprofile von Einsatzkraeften
- **Audit-Logs:** Koennten IP-Adressen und Nutzungsverhalten offenlegen

---

## 6. Meldung an die Aufsichtsbehoerde (Art. 33 DSGVO)

### 6.1 Frist

**72 Stunden** nach Kenntniserlangung der Datenschutzverletzung.

### 6.2 Zustaendige Aufsichtsbehoerde

- **Deutschland:** [Landesdatenschutzbehoerde des Bundeslandes]
- **Oesterreich:** Oesterreichische Datenschutzbehoerde (DSB)

### 6.3 Melde-Vorlage

```
MELDUNG EINER DATENSCHUTZVERLETZUNG
gemaess Art. 33 DSGVO

An: [Aufsichtsbehoerde]
Von: [Verantwortlicher]
Datum: ___.___.______
Aktenzeichen (falls vorhanden): ________________

1. BESCHREIBUNG DER VERLETZUNG

1.1 Art der Verletzung:
[ ] Unbefugter Zugang
[ ] Unbefugte Offenlegung
[ ] Verlust/Vernichtung
[ ] Unbefugte Veraenderung

1.2 Beschreibung des Vorfalls:
___________________________________________________________________
___________________________________________________________________

1.3 Zeitpunkt der Verletzung: ___.___.______ __:__ Uhr
1.4 Zeitpunkt der Kenntniserlangung: ___.___.______ __:__ Uhr

2. BETROFFENE PERSONEN UND DATEN

2.1 Kategorien betroffener Personen:
[ ] Patienten
[ ] Einsatzkraefte
[ ] Leitstellenpersonal
[ ] Sonstige: ________

2.2 Ungefaehre Anzahl betroffener Personen: ________

2.3 Kategorien betroffener Daten:
[ ] Name, Kontaktdaten
[ ] Gesundheitsdaten (Art. 9 DSGVO)
[ ] Standortdaten
[ ] Login-/Authentifizierungsdaten
[ ] Kommunikationsdaten
[ ] Sonstige: ________

2.4 Ungefaehre Anzahl betroffener Datensaetze: ________

3. WAHRSCHEINLICHE FOLGEN

___________________________________________________________________
___________________________________________________________________

4. ERGRIFFENE MASSNAHMEN

4.1 Sofortmassnahmen:
___________________________________________________________________

4.2 Geplante Massnahmen:
___________________________________________________________________

4.3 Massnahmen zur Abmilderung der Folgen:
___________________________________________________________________

5. KONTAKTDATEN

5.1 Datenschutzbeauftragter:
Name: _________________________
E-Mail: _______________________
Telefon: ______________________

5.2 Ansprechpartner fuer Rueckfragen:
Name: _________________________
E-Mail: _______________________
Telefon: ______________________

6. ERGAENZENDE INFORMATIONEN

[ ] Erste Meldung (weitere Informationen folgen)
[ ] Aktualisierung einer vorherigen Meldung vom ___.___.______
[ ] Abschliessende Meldung

Unterschrift: _________________________
```

---

## 7. Benachrichtigung betroffener Personen (Art. 34 DSGVO)

### 7.1 Wann ist eine Benachrichtigung erforderlich?

Wenn die Datenschutzverletzung voraussichtlich ein **hohes Risiko** fuer die Rechte und Freiheiten der betroffenen Personen zur Folge hat.

### 7.2 Ausnahmen (Art. 34 Abs. 3 DSGVO)

Eine Benachrichtigung ist nicht erforderlich, wenn:
- **a)** Daten verschluesselt waren (Fernet-Verschluesselung in OpMan_GPT)
- **b)** Massnahmen das Risiko beseitigt haben
- **c)** Oeffentliche Bekanntmachung bei unverhaeltnismaessigem Aufwand

### 7.3 Benachrichtigungs-Vorlage

```
Betreff: Wichtige Information zum Schutz Ihrer Daten

Sehr geehrte/r [Betroffene Person],

wir informieren Sie gemaess Art. 34 der Datenschutz-Grundverordnung
darueber, dass es zu einer Verletzung des Schutzes Ihrer
personenbezogenen Daten gekommen ist.

WAS IST PASSIERT?
___________________________________________________________________

WELCHE DATEN SIND BETROFFEN?
___________________________________________________________________

WELCHE FOLGEN KOENNEN ENTSTEHEN?
___________________________________________________________________

WAS HABEN WIR UNTERNOMMEN?
___________________________________________________________________

WAS KOENNEN SIE TUN?
- Aendern Sie Ihre Passwoerter fuer alle Konten, bei denen Sie
  aehnliche Zugangsdaten verwenden
- Achten Sie auf verdaechtige Aktivitaeten
- [Weitere Empfehlungen je nach Art der Panne]

KONTAKT
Bei Fragen wenden Sie sich bitte an unseren Datenschutzbeauftragten:
[Name, E-Mail, Telefon]

Sie haben zudem das Recht, sich bei der zustaendigen Datenschutz-
Aufsichtsbehoerde zu beschweren:
[Name und Kontakt der Aufsichtsbehoerde]

Mit freundlichen Gruessen,
[Verantwortlicher]
```

---

## 8. Interne Dokumentation

### 8.1 Dokumentationspflicht (Art. 33 Abs. 5 DSGVO)

Unabhaengig von der Meldepflicht muss **jede** Datenschutzverletzung intern dokumentiert werden.

### 8.2 Dokumentations-Template

| Feld | Inhalt |
|------|--------|
| Vorfallnummer | BREACH-____-____ |
| Entdeckungsdatum | ___.___.______ |
| Entdecker | |
| Art der Verletzung | |
| Betroffene Systeme | |
| Betroffene Daten | |
| Anzahl Betroffene | |
| Ursache | |
| Sofortmassnahmen | |
| Risikobewertung | [ ] Kein Risiko [ ] Risiko [ ] Hohes Risiko |
| Meldung Aufsichtsbehoerde | [ ] Ja, am ___.___.___ [ ] Nein (Begruendung: ___) |
| Benachrichtigung Betroffene | [ ] Ja, am ___.___.___ [ ] Nein (Begruendung: ___) |
| NIS2-Meldung (BSI/BACYS) | [ ] Ja, am ___.___.___ [ ] Nein |
| Korrekturmassnahmen | |
| Abschluss | ___.___.______ |
| Verantwortlich | |

---

## 9. Automatische Breach-Erkennung in OpMan_GPT

OpMan_GPT verfuegt ueber eine integrierte Breach-Erkennungsfunktion (`/api/dsgvo/check-breach`), die folgende Indikatoren prueft:

| Indikator | Schwelle | Schweregrad |
|-----------|---------|-------------|
| Uebertriebene Datenexporte | > 10 in 24h | MEDIUM / HIGH |
| Massen-Datenzugriffe | > 100 in 24h | MEDIUM / HIGH |
| Abgelehnte Zugriffsversuche | > 5 in 24h | HIGH / CRITICAL |
| Fehlgeschlagene Logins | > 10 in 24h | HIGH / CRITICAL |
| Ungewoehnliche Loeschungen | > 5 in 24h | MEDIUM |

Das DSGVO-Dashboard zeigt den aktuellen Breach-Status und loest bei HIGH/CRITICAL eine Warnung aus.

---

## 10. Uebung und Tests

- **Turnus:** Halbjaehrlich eine Breach-Notification-Uebung
- **Inhalt:** Durchspielen des gesamten Meldeprozesses (intern + simulierte Behoerdenmeldung)
- **Dokumentation:** Uebungsergebnisse und Verbesserungsmassnahmen

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
