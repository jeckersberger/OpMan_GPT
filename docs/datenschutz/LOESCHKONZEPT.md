# Loeschkonzept

**Dokument:** Datenloeschkonzept gemaess Art. 17 DSGVO, Art. 5(1)(e) DSGVO
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich

---

## 1. Zweck

Dieses Loeschkonzept definiert die Aufbewahrungsfristen fuer alle personenbezogenen Daten in OpMan_GPT sowie die Verfahren zur regelmaessigen und anlassbezogenen Loeschung bzw. Anonymisierung.

**Grundsatz:** Personenbezogene Daten werden geloescht, sobald der Zweck der Verarbeitung entfaellt und keine gesetzlichen Aufbewahrungspflichten der Loeschung entgegenstehen (Art. 5(1)(e) DSGVO -- Speicherbegrenzung).

---

## 2. Aufbewahrungsfristen

### 2.1 Fristen nach Datenart

| Datenart | Aufbewahrungsfrist | Rechtsgrundlage | Loeschart |
|----------|-------------------|-----------------|-----------|
| **Patientendaten (Echtbetrieb)** | 10 Jahre ab Einsatzende | Rettungsdienstgesetz, GuKG | Anonymisierung |
| **Patientendaten (Uebung)** | 365 Tage (konfigurierbar) | Berechtigtes Interesse | Anonymisierung |
| **Gesundheitsdaten (Vitalzeichen)** | 10 Jahre ab Einsatzende | Art. 9(2)(h), RettDG | Loeschung/Anonymisierung |
| **GPS-Standortdaten** | 90 Tage | Datenminimierung | Loeschung |
| **Funkprotokolle** | 1 Jahr | RettDG Dokumentationspflicht | Loeschung |
| **Audit-Logs** | 3 Jahre | BSIG/NIS2, Revisionsanforderungen | Detail-Bereinigung |
| **Benutzerdaten** | Dauer Konto + 3 Jahre | Nachweispflicht | Loeschung |
| **Einwilligungen** | 3 Jahre nach Widerruf | Art. 7(1) Nachweispflicht | Loeschung |
| **Pseudonym-Mappings** | Identisch mit Falldokumentation | Zweckbindung | Loeschung |
| **Web-Push-Abonnements** | Bis Abmeldung/Geraetewechsel | Zweckentfall | Loeschung |
| **Session-Daten** | 30 Minuten Inaktivitaet | Session-Timeout | Automatische Loeschung |
| **Break-Glass-Logs** | 3 Jahre | Revisionsanforderung | Archivierung |

### 2.2 Fristen nach Datenbanktabelle

| Tabelle | Personenbezug | Frist | Automatisch? |
|---------|-------------|-------|-------------|
| `case_definitions` | Ja (Patient, Gesundheit) | 365 Tage (Uebung) / 10 Jahre (Echtbetrieb) | Ja (auto-cleanup) |
| `case_docs` | Indirekt | Wie case_definitions | Ja |
| `teams` | Ja (Einsatzkraefte) | Sessiondauer | Manuell |
| `missions` | Indirekt | Wie case_definitions | Ja |
| `assignments` | Indirekt | Wie case_definitions | Ja |
| `radio_log` | Ja (Funksprueche) | 1 Jahr | Manuell |
| `users` | Ja (Benutzerdaten) | Konto + 3 Jahre | Manuell |
| `user_sessions` | Ja (IP, User-Agent) | 30 Min Inaktivitaet | Automatisch |
| `audit_log` | Ja (Benutzername, IP) | 3 Jahre | Ja (data-retention API) |
| `consent_records` | Ja (Betroffener) | 3 Jahre nach Widerruf | Manuell |
| `pseudonym_mappings` | Nein (nur Hashes) | Wie zugehoeriger Fall | Automatisch |
| `push_subscriptions` | Ja (Endpoint) | Bis Abmeldung | Manuell |
| `break_glass_log` | Ja (Benutzer) | 3 Jahre | Manuell |

---

## 3. Automatische Loeschregeln

### 3.1 Auto-Cleanup (implementiert in dsgvo.py)

**Endpunkt:** `POST /api/dsgvo/auto-cleanup`

**Funktion:** Anonymisiert alle Faelle, deren `updated_at` aelter als die konfigurierte Aufbewahrungsfrist ist.

**Anonymisierung:**
```
patient       -> "GELOESCHT"
patient_alarm -> "GELOESCHT"
alter         -> NULL
geschlecht    -> NULL
besonderheit  -> NULL
hinweis       -> NULL
```

**Audit-Log-Bereinigung:** Details aelterer Audit-Eintraege werden durch "[BEREINIGT]" ersetzt. Die Struktur (Zeitstempel, Aktion, Benutzer) bleibt fuer Revisionszwecke erhalten.

**Konfiguration:**
- Standard-Aufbewahrungsfrist: 365 Tage
- Konfigurierbar ueber `DSGVO_RETENTION_DAYS` in der App-Konfiguration
- Manuell auslösbar ueber DSGVO-Dashboard

### 3.2 Data Retention API (implementiert in auth.py)

**Endpunkt:** `POST /api/admin/data-retention`

**Funktion:** Loescht Audit-Log-Eintraege aelter als die angegebene Frist.

**Parameter:** `retention_days` (Standard: 365)

### 3.3 Empfohlener automatisierter Zeitplan

| Aufgabe | Turnus | Methode |
|---------|--------|---------|
| Auto-Cleanup (Falldaten) | Woechtentlich | Cronjob: `curl -X POST /api/dsgvo/auto-cleanup` |
| Audit-Log Retention | Monatlich | Cronjob: `curl -X POST /api/admin/data-retention` |
| GPS-Daten bereinigen | Taeglich | Datenbank-Job (zu implementieren) |
| Inaktive Sessions loeschen | Stuendlich | Datenbank-Job (zu implementieren) |
| Push-Subscriptions pruefen | Woechtentlich | Ungueltige Endpunkte entfernen |

---

## 4. Manuelle Loeschprozesse

### 4.1 Loeschung auf Antrag (Art. 17 DSGVO)

**Prozess:**

1. Eingang des Loeschantrags dokumentieren (Audit-Log)
2. Identitaet des Antragstellers verifizieren
3. Pruefen, ob gesetzliche Aufbewahrungspflichten der Loeschung entgegenstehen
4. Falls keine Aufbewahrungspflicht:
   - Einzelfall-Anonymisierung ueber `DELETE /api/dsgvo/personal-data/<case_id>`
   - Zugehoerige Pseudonym-Mappings loeschen
   - Zugehoerige Einwilligungen als "Zweck entfallen" markieren
5. Falls Aufbewahrungspflicht besteht:
   - Antragsteller ueber Aufbewahrungspflicht informieren
   - Einschraenkung der Verarbeitung (Art. 18 DSGVO) pruefen
   - Loeschung nach Ablauf der Frist vormerken
6. Antwort an Antragsteller innerhalb von **1 Monat** (Art. 12(3) DSGVO)
7. Loeschung im Audit-Log dokumentieren

**Antwort-Vorlage:**

> Sehr geehrte/r [Name],
>
> wir bestaetigen den Eingang Ihres Loeschantrags vom [Datum].
>
> [ ] Ihre personenbezogenen Daten wurden anonymisiert.
> [ ] Eine Loeschung ist derzeit aufgrund gesetzlicher Aufbewahrungspflichten
>     (Rettungsdienstgesetz, Aufbewahrungsfrist: [X] Jahre) nicht moeglich.
>     Die Daten werden nach Ablauf der Frist automatisch anonymisiert.
>     Die Verarbeitung wurde auf das gesetzlich erforderliche Mass eingeschraenkt.
>
> Mit freundlichen Gruessen,
> [Datenschutzbeauftragter]

### 4.2 Loeschung bei Kontodeaktivierung

Wenn ein Benutzerkonto deaktiviert wird:

1. Konto als inaktiv markieren (`is_active_user = False`)
2. MFA-Secret loeschen
3. Aktive Sessions beenden
4. Nach 3 Jahren: Konto und zugehoerige Daten loeschen
5. Audit-Log-Eintraege bleiben fuer Revisionszwecke erhalten (Detail-Bereinigung nach 3 Jahren)

### 4.3 Loeschung bei Systemausserbetriebnahme

Bei vollstaendiger Ausserbetriebnahme von OpMan_GPT:

1. Datenexport fuer gesetzliche Aufbewahrungspflichten erstellen (verschluesselt)
2. Alle personenbezogenen Daten aus der Datenbank loeschen
3. Verschluesselungsschluessel sicher vernichten
4. Datentraeger sicher loeschen (mindestens 1x Ueberschreiben, besser: physische Vernichtung)
5. Loeschung dokumentieren und Nachweis aufbewahren

---

## 5. Anonymisierungsverfahren

### 5.1 Pseudonymisierung (reversibel)

- Patientennamen werden durch generierte Pseudonyme ersetzt (z.B. "Patient-A7F3C2")
- Zuordnungstabelle wird getrennt gespeichert
- Original wird als SHA-256-Hash gespeichert
- Re-Identifizierung nur durch autorisierte Rollen moeglich

### 5.2 Anonymisierung (irreversibel)

- Personenbezogene Felder werden durch "GELOESCHT" ersetzt
- Numerische Felder (Alter) werden auf NULL gesetzt
- Pseudonym-Mapping wird geloescht
- Keine Re-Identifizierung moeglich
- Sachliche Einsatzdaten (Schlagwort, Zeitstempel, Prioritaet) bleiben fuer statistische Auswertung erhalten

---

## 6. Technische Loeschmethoden

| Medium | Methode | Standard |
|--------|---------|---------|
| SQLite-Datenbank | UPDATE (Anonymisierung) + VACUUM | Logische Loeschung |
| PostgreSQL-Datenbank | UPDATE + DELETE | Logische Loeschung |
| Dateisystem (Schluessel) | Sicheres Loeschen (shred) | DIN 66399 |
| Festplatten | 1x Ueberschreiben (HDD) / Secure Erase (SSD) | DIN 66399 Sicherheitsstufe 3 |
| Backups | Verschluesselte Backups nach Frist loeschen | AES-256 |
| Papier | Aktenvernichter Stufe P-4 | DIN 66399 |

---

## 7. Verantwortlichkeiten

| Aufgabe | Verantwortlich |
|---------|---------------|
| Ueberwachung der Aufbewahrungsfristen | Datenschutzbeauftragter |
| Durchfuehrung automatischer Loeschungen | IT-Administration |
| Bearbeitung von Loeschantraegen | Datenschutzbeauftragter |
| Jaehrliche Ueberpruefung des Loeschkonzepts | DSB + ISB |
| Nachweis der Loeschung | IT-Administration |

---

## 8. Dokumentation und Nachweis

Alle Loeschvorgaenge werden im Audit-Log dokumentiert:
- `DSGVO_ERASURE`: Einzelfall-Anonymisierung
- `DSGVO_AUTO_CLEANUP`: Automatische Bereinigung
- `DATA_RETENTION_EXECUTED`: Audit-Log-Retention
- `DSGVO_CONSENT_DELETED`: Einwilligungsloeschung

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
