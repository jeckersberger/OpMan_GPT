# Verzeichnis der Verarbeitungstaetigkeiten

**Dokument:** Verarbeitungsverzeichnis gemaess Art. 30 DSGVO
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich

---

## Angaben zum Verantwortlichen (Art. 30 Abs. 1 lit. a)

| Feld | Angabe |
|------|--------|
| **Name des Verantwortlichen** | [Organisation / Rettungsdienst] |
| **Anschrift** | [Strasse, PLZ, Ort] |
| **Vertreter** | [Name, Kontaktdaten] |
| **Datenschutzbeauftragter** | [Name, E-Mail, Telefon] |

---

## Verarbeitungstaetigkeit 1: Einsatzkoordination und Disposition

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Einsatzkoordination und Trupp-Disposition |
| **Verantwortlich** | Leitstellenleitung / Disponent |
| **Zweck** | Zuordnung von Rettungsteams zu Einsaetzen, Statusueberwachung |
| **Rechtsgrundlage** | Art. 6(1)(e) DSGVO i.V.m. Rettungsdienstgesetz (oeffentliche Aufgabe) |
| **Betroffene Personen** | Einsatzkraefte (EVT-Operatoren), Disponenten |
| **Datenkategorien** | Teamname, Rufname, Funkstatus (FMS 0-9), Verfuegbarkeit, Funkgruppe, Fahrzeugkennung |
| **Empfaenger** | Leitstellenpersonal, Einsatzleiter |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | Einsatzdaten: 10 Jahre (RettDG); Uebungsdaten: 1 Jahr |
| **TOM-Verweis** | Siehe TOM.md |
| **Datenbank-Tabelle** | `teams`, `missions`, `assignments` |

---

## Verarbeitungstaetigkeit 2: Patientendaten-Erfassung

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Erfassung und Verarbeitung von Patientendaten |
| **Verantwortlich** | Einsatzleiter / Disponent |
| **Zweck** | Dokumentation der Patientenversorgung, Uebergabe an Klinik, Qualitaetssicherung |
| **Rechtsgrundlage** | Art. 6(1)(e) DSGVO i.V.m. RettDG; Art. 9(2)(c) (lebenswichtiges Interesse); Art. 9(2)(h) (Gesundheitsversorgung) |
| **Betroffene Personen** | Patienten (Notfallpatienten) |
| **Datenkategorien** | Name, Alarmierungsname, Alter, Geschlecht, **Vitalparameter (Art. 9)**, Besonderheiten (Allergien, Vorerkrankungen), ABCD-Schema |
| **Empfaenger** | EVT-Teams, Aerztlicher Leiter, aufnehmende Klinik |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | 10 Jahre (RettDG); Uebungsdaten: 1 Jahr |
| **TOM-Verweis** | Fernet-Verschluesselung der Patientennamen, RBAC, Pseudonymisierung |
| **Datenbank-Tabelle** | `case_definitions`, `case_docs` |
| **Besonderheit** | Gesundheitsdaten gemaess Art. 9 DSGVO -- erhoehter Schutzbedarf |

---

## Verarbeitungstaetigkeit 3: GPS-Tracking der Einsatzteams

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | GPS-Standorterfassung der Einsatzteams |
| **Verantwortlich** | Leitstellenleitung |
| **Zweck** | Lokalisierung der Einsatzteams fuer optimale Disposition, Anfahrtszeitschaetzung |
| **Rechtsgrundlage** | Art. 6(1)(f) DSGVO (berechtigtes Interesse: effektive Notfallversorgung) |
| **Betroffene Personen** | Einsatzkraefte (EVT-Operatoren) |
| **Datenkategorien** | GPS-Koordinaten (Laengen-/Breitengrad), Zeitstempel, Team-Zuordnung |
| **Empfaenger** | Leitstellenpersonal (Disponenten, Schichtleiter) |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | 90 Tage (Datenminimierung) |
| **TOM-Verweis** | RBAC (nur Leitstellenpersonal), automatische Loeschung |
| **Datenbank-Tabelle** | `teams` (lat, lng Felder) |
| **Interessenabwaegung** | Interesse an effektiver Notfallversorgung ueberwiegt Interesse der Beschaeftigten an Standort-Privatsphaere waehrend des Dienstes; GPS-Tracking nur waehrend aktiver Schicht; Information der Beschaeftigten erfolgt |

---

## Verarbeitungstaetigkeit 4: Funkprotokoll

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Protokollierung von Funkkommunikation und Statusmeldungen |
| **Verantwortlich** | Leitstellenleitung |
| **Zweck** | Chronologische Dokumentation aller Funksprueche und Statuswechsel |
| **Rechtsgrundlage** | Art. 6(1)(c) DSGVO (rechtliche Verpflichtung: RettDG Dokumentationspflicht) |
| **Betroffene Personen** | Einsatzkraefte, indirekt: Patienten |
| **Datenkategorien** | Teamname, Rufname, Nachrichteninhalt, Statuswechsel, Zeitstempel, Fall-Zuordnung |
| **Empfaenger** | Leitstellenpersonal, bei Bedarf: Aufsichtsbehoerde |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | 1 Jahr |
| **TOM-Verweis** | RBAC, Audit-Log |
| **Datenbank-Tabelle** | `radio_log` |

---

## Verarbeitungstaetigkeit 5: Benutzerverwaltung und Authentifizierung

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Verwaltung von Benutzerkonten, Authentifizierung, Autorisierung |
| **Verantwortlich** | IT-Administration |
| **Zweck** | Zugangssteuerung, Identitaetspruefung, Rollenbasierte Rechtevergabe |
| **Rechtsgrundlage** | Art. 6(1)(b) DSGVO (Vertragserfullung / Beschaeftigungsverhaeltnis) |
| **Betroffene Personen** | Alle Systembenutzer |
| **Datenkategorien** | Benutzername, Passwort-Hash (bcrypt), Rolle, Anzeigename, MFA-Secret (TOTP), Letzter Login, Fehlversuche, Sperrungsstatus, IP-Adresse |
| **Empfaenger** | Administratoren |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | Dauer des Kontos + 3 Jahre (Nachweispflicht) |
| **TOM-Verweis** | bcrypt-Hashing, MFA (TOTP), Account-Sperrung, Session-Limiting |
| **Datenbank-Tabelle** | `users`, `user_sessions` |

---

## Verarbeitungstaetigkeit 6: Audit-Protokollierung

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Revisionssichere Protokollierung sicherheitsrelevanter Aktionen |
| **Verantwortlich** | IT-Sicherheitsbeauftragter |
| **Zweck** | Nachvollziehbarkeit, Compliance, Forensik, Manipulationserkennung |
| **Rechtsgrundlage** | Art. 6(1)(c) DSGVO (rechtliche Verpflichtung: BSIG, NIS2); Art. 6(1)(f) (berechtigtes Interesse: IT-Sicherheit) |
| **Betroffene Personen** | Alle Systembenutzer |
| **Datenkategorien** | Zeitstempel, Benutzer-ID, Benutzername, Aktion, Ressource, Details, IP-Adresse, User-Agent, Hash (SHA-256 Chain) |
| **Empfaenger** | Administratoren, IS-Beauftragter, DSB, bei Bedarf: Aufsichtsbehoerde |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | 3 Jahre (BSIG/NIS2); Detail-Bereinigung nach konfigurierbarer Frist |
| **TOM-Verweis** | Hash-Chain (Integritaetsschutz), RBAC (Einsicht nur fuer admin/schichtleiter/datenschutz) |
| **Datenbank-Tabelle** | `audit_log` |

---

## Verarbeitungstaetigkeit 7: Einwilligungsverwaltung

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Erfassung und Verwaltung von Einwilligungen (Consent Management) |
| **Verantwortlich** | Datenschutzbeauftragter |
| **Zweck** | Dokumentation erteilter und widerrufener Einwilligungen (Art. 7 DSGVO) |
| **Rechtsgrundlage** | Art. 7(1) DSGVO (Nachweispflicht fuer Einwilligungen) |
| **Betroffene Personen** | Patienten, Einsatzkraefte |
| **Datenkategorien** | Betroffener (data_subject), Zweck (purpose), Erteilungsdatum, Widerrufsdatum, Rechtsgrundlage |
| **Empfaenger** | DSB, Administratoren |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | 3 Jahre nach Widerruf |
| **TOM-Verweis** | RBAC (nur DSGVO-Rollen), Audit-Log |
| **Datenbank-Tabelle** | `consent_records` |

---

## Verarbeitungstaetigkeit 8: Pseudonymisierung

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Pseudonymisierung personenbezogener Daten |
| **Verantwortlich** | Datenschutzbeauftragter / System |
| **Zweck** | Datenschutz durch Trennung von Identifizierungsdaten (Art. 4 Nr. 5, Art. 25 DSGVO) |
| **Rechtsgrundlage** | Art. 6(1)(c) DSGVO (Art. 25 Datenschutz durch Technikgestaltung) |
| **Betroffene Personen** | Patienten |
| **Datenkategorien** | Original-Hash (SHA-256), Pseudonym (Patient-XXXXXX), Erstellungszeitpunkt |
| **Empfaenger** | System-intern (Zuordnungstabelle getrennt gespeichert) |
| **Drittlandtransfer** | Nein |
| **Aufbewahrungsfrist** | Identisch mit zugehoeriger Falldokumentation |
| **TOM-Verweis** | Getrennte Speicherung des Mappings, RBAC |
| **Datenbank-Tabelle** | `pseudonym_mappings` |

---

## Verarbeitungstaetigkeit 9: Web-Push-Benachrichtigungen

| Feld | Beschreibung |
|------|-------------|
| **Bezeichnung** | Push-Benachrichtigungen fuer Einsatzalarmierung |
| **Verantwortlich** | IT-Administration |
| **Zweck** | Alarmierung der Einsatzteams ueber Web Push API |
| **Rechtsgrundlage** | Art. 6(1)(f) DSGVO (berechtigtes Interesse: zeitkritische Alarmierung) |
| **Betroffene Personen** | EVT-Operatoren |
| **Datenkategorien** | Push-Endpoint (URL), Schluessel (p256dh, auth), EVT-Name |
| **Empfaenger** | Browser des Empfaengers (ueber VAPID-Protokoll) |
| **Drittlandtransfer** | Push-Endpunkte koennen ueber Push-Services der Browser-Hersteller laufen (Google FCM, Mozilla Push). Technisch unvermeidbar. |
| **Aufbewahrungsfrist** | Bis zur Abmeldung des Geraetes |
| **TOM-Verweis** | VAPID-Authentifizierung, Verschluesselung der Push-Payload |
| **Datenbank-Tabelle** | `push_subscriptions` |

---

## Zusammenfassung der Verarbeitungstaetigkeiten

| Nr. | Taetigkeit | Art. 9 Daten | Rechtsgrundlage | Aufbewahrung |
|-----|-----------|-------------|-----------------|-------------|
| 1 | Einsatzkoordination | Nein | Art. 6(1)(e) | 10 Jahre |
| 2 | Patientendaten | **Ja** | Art. 6(1)(e), Art. 9(2)(c)(h) | 10 Jahre |
| 3 | GPS-Tracking | Nein | Art. 6(1)(f) | 90 Tage |
| 4 | Funkprotokoll | Nein | Art. 6(1)(c) | 1 Jahr |
| 5 | Benutzerverwaltung | Nein | Art. 6(1)(b) | Dauer + 3 J. |
| 6 | Audit-Protokollierung | Nein | Art. 6(1)(c)(f) | 3 Jahre |
| 7 | Einwilligungsverwaltung | Nein | Art. 7(1) | 3 J. nach Widerruf |
| 8 | Pseudonymisierung | Nein | Art. 6(1)(c) | Wie Falldoku |
| 9 | Web-Push | Nein | Art. 6(1)(f) | Bis Abmeldung |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
