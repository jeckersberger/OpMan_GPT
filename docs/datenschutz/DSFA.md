# Datenschutz-Folgenabschaetzung (DSFA)

**Dokument:** DSFA gemaess Art. 35 DSGVO
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Vertraulich
**Verantwortlicher:** [Name des Verantwortlichen]
**Datenschutzbeauftragter:** [Name DSB]

---

## 1. Beschreibung der Verarbeitungsvorgaenge

### 1.1 Systemuebersicht

**OpMan_GPT** ist eine webbasierte Einsatzleitsoftware fuer den Sanitaetsdienst und Rettungsdienst. Das System verarbeitet personenbezogene Daten in folgenden Bereichen:

- Patientendaten (Name, Alter, Geschlecht, Gesundheitszustand)
- Einsatzdaten (Ort, Zeit, Art des Einsatzes)
- GPS-Standortdaten der Einsatzteams
- Funkprotokolle und Statusmeldungen
- Benutzerdaten (Logins, Rollen, Aktionen)
- Audit-Protokolle (Zugriffe, Aenderungen)

### 1.2 Zweck der Verarbeitung

| Zweck | Beschreibung | Rechtsgrundlage |
|-------|-------------|-----------------|
| Einsatzkoordination | Zuordnung von Rettungsteams zu Einsaetzen | Art. 6(1)(e) DSGVO, Rettungsdienstgesetz |
| Patientendokumentation | Erfassung medizinischer Erstversorgungsdaten | Art. 9(2)(c) DSGVO (lebenswichtiges Interesse), RettDG |
| GPS-Tracking | Standorterfassung der Einsatzfahrzeuge/Teams | Art. 6(1)(f) DSGVO (berechtigtes Interesse) |
| Funkprotokoll | Dokumentation der Funkkommunikation | Art. 6(1)(c) DSGVO (rechtliche Verpflichtung) |
| Benutzerverwaltung | Authentifizierung und Autorisierung | Art. 6(1)(b) DSGVO (Vertragserfullung) |
| Audit-Logging | Revisionssichere Protokollierung | Art. 6(1)(c) DSGVO (rechtliche Verpflichtung) |
| Qualitaetssicherung | Auswertung von Einsaetzen (Uebung) | Art. 6(1)(f) DSGVO (berechtigtes Interesse) |

### 1.3 Kategorien betroffener Personen

- **Patienten**: Personen, fuer die ein Rettungseinsatz durchgefuehrt wird
- **Einsatzkraefte**: Rettungsdienst-Mitarbeiter, EVT-Operatoren
- **Disponenten / Leitstellenpersonal**: Benutzer des Systems
- **Administratoren**: IT-Personal mit Systemzugang

### 1.4 Kategorien personenbezogener Daten

| Kategorie | Datenfelder | Besondere Kategorie (Art. 9) |
|-----------|------------|------------------------------|
| Patientenidentifikation | Name, Alarmierungsname | Nein |
| Gesundheitsdaten | Alter, Geschlecht, Vitalzeichen (vitals_json), Besonderheiten, ABCD-Schema | **Ja (Art. 9)** |
| Standortdaten | GPS-Koordinaten, Einsatzort | Nein |
| Beschaeftigtendaten | Benutzername, Rolle, IP-Adresse, Login-Zeiten | Nein |
| Kommunikationsdaten | Funkprotokolle, Statusmeldungen | Nein |
| Protokolldaten | Audit-Logs (Aktionen, Zeitstempel, IP) | Nein |

### 1.5 Empfaenger der Daten

| Empfaenger | Zweck | Rechtsgrundlage |
|-----------|-------|-----------------|
| Leitstellenpersonal | Einsatzkoordination | Rettungsdienstgesetz |
| Rettungsteams (EVT) | Einsatzdurchfuehrung | Rettungsdienstgesetz |
| Aerztlicher Leiter | Medizinische Qualitaetssicherung | Rettungsdienstgesetz |
| Datenschutzbeauftragter | Audit, Compliance-Pruefung | Art. 39 DSGVO |
| Aufsichtsbehoerde | Bei Datenpannen / auf Anfrage | Art. 33, 58 DSGVO |

### 1.6 Aufbewahrungsfristen

| Datenart | Frist | Grundlage |
|----------|-------|-----------|
| Patientendaten (Echtbetrieb) | 10 Jahre | Rettungsdienstgesetz |
| Patientendaten (Uebung) | 1 Jahr (konfigurierbar) | Berechtigtes Interesse |
| GPS-Daten | 90 Tage | Datenminimierung |
| Funkprotokolle | 1 Jahr | Rettungsdienstgesetz |
| Audit-Logs | 3 Jahre | NIS2, BSIG |
| Benutzerdaten | Dauer des Beschaeftigungsverhaeltnisses + 3 Jahre | Arbeitsrecht |

### 1.7 Drittlandtransfer

**Kein Drittlandtransfer.** OpMan_GPT wird vollstaendig lokal im LAN betrieben. Es werden keine Daten an Cloud-Dienste oder Dienstleister ausserhalb der EU uebermittelt.

Einzige externe Verbindung: OpenStreetMap-Kartenkacheln (reine Anzeige, keine personenbezogenen Daten).

---

## 2. Notwendigkeit und Verhaeltnismaessigkeit

### 2.1 Notwendigkeit der Verarbeitung

Die Verarbeitung ist notwendig fuer:

- **Lebensrettung:** Ohne Einsatzkoordinierung koennen Patienten nicht rechtzeitig versorgt werden
- **Gesetzliche Pflicht:** Rettungsdienstgesetze schreiben Dokumentation vor
- **Qualitaetssicherung:** Medizinische Erstversorgung erfordert Nachverfolgbarkeit
- **Accountability:** NIS2/BSIG verlangen revisionssichere Protokollierung

### 2.2 Verhaeltnismaessigkeitspruefung

| Grundsatz | Umsetzung in OpMan_GPT |
|-----------|----------------------|
| Datenminimierung (Art. 5(1)(c)) | Nur fuer Einsatz erforderliche Daten werden erhoben; Datenminimierungsbericht implementiert |
| Zweckbindung (Art. 5(1)(b)) | Daten werden nur fuer Einsatzkoordination und gesetzl. Dokumentation verwendet |
| Speicherbegrenzung (Art. 5(1)(e)) | Automatische Anonymisierung nach Aufbewahrungsfrist (auto-cleanup) |
| Richtigkeit (Art. 5(1)(d)) | Echtzeit-Updates, Audit-Trail fuer Aenderungen |
| Integritaet (Art. 5(1)(f)) | Hash-Chain Audit-Log, Fernet-Verschluesselung, RBAC |
| Rechenschaftspflicht (Art. 5(2)) | Vollstaendiges Audit-Logging, DSGVO-Dashboard |

### 2.3 Weniger eingriffsintensive Alternativen

| Alternative | Bewertung |
|------------|-----------|
| Papierbasierte Dokumentation | Nicht praktikabel fuer Echtzeitkoordination; hoeheres Verlustrisiko |
| Vollstaendige Pseudonymisierung | Nicht moeglich, da Patientenidentifikation fuer Uebergabe an Klinik erforderlich |
| Keine GPS-Erfassung | Wuerde Einsatzkoordination erheblich verschlechtern |
| Zentrale Cloud-Loesung | Hoeheres Risiko (Drittlandtransfer, Verfuegbarkeit), OpMan_GPT laeuft bewusst lokal |

---

## 3. Risikobewertung

### 3.1 Risiko-Matrix

**Bewertungsskala:**
- Eintrittswahrscheinlichkeit: 1 (sehr gering) - 4 (sehr hoch)
- Schadenshoehe: 1 (gering) - 4 (sehr hoch)
- Risiko = Eintrittswahrscheinlichkeit x Schadenshoehe

### 3.2 Identifizierte Risiken

| Nr. | Risiko | Betroffene | EW | SH | Risiko | Massnahme |
|-----|--------|-----------|----|----|--------|-----------|
| R1 | Unbefugter Zugriff auf Patientendaten | Patienten | 2 | 4 | 8 (Hoch) | RBAC, MFA, Verschluesselung, Session-Limiting |
| R2 | Datenverlust durch Systemausfall | Patienten, Einsatzkraefte | 2 | 4 | 8 (Hoch) | Backup, BCM-Plan, SQLite WAL-Mode |
| R3 | Manipulation von Audit-Logs | Alle | 1 | 4 | 4 (Mittel) | Hash-Chain, getrennte Speicherung |
| R4 | Unbefugte GPS-Ueberwachung | Einsatzkraefte | 2 | 3 | 6 (Mittel) | RBAC, nur autorisierte Einsicht, Auto-Loeschung |
| R5 | Brute-Force-Angriff auf Login | Alle | 3 | 3 | 9 (Hoch) | Account-Sperrung, Rate Limiting, Anomalie-Erkennung |
| R6 | Insider-Missbrauch (Datenexport) | Patienten | 2 | 4 | 8 (Hoch) | Audit-Log, Breach-Erkennung, rollenbasierter Export |
| R7 | Verlust des Verschluesselungsschluessels | Patienten | 1 | 4 | 4 (Mittel) | Schluessel-Backup, HSM-Evaluation |
| R8 | Identitaetsdiebstahl (Session-Hijacking) | Benutzer | 2 | 3 | 6 (Mittel) | Secure Cookies, CSRF-Schutz, Session-Timeout |
| R9 | Physischer Zugriff auf Server | Alle | 1 | 4 | 4 (Mittel) | Zutrittskontrolle, Festplattenverschluesselung |
| R10 | DSGVO-Verstoss (uebermaessige Speicherung) | Patienten | 2 | 3 | 6 (Mittel) | Auto-Cleanup, Loeschkonzept, Aufbewahrungsfristen |

### 3.3 Risikobewertung Gesundheitsdaten (Art. 9 DSGVO)

**Besondere Risikobewertung fuer Gesundheitsdaten:**

OpMan_GPT verarbeitet Gesundheitsdaten (Art. 9 DSGVO), insbesondere:
- Vitalparameter (vitals_json)
- Alter und Geschlecht im medizinischen Kontext
- ABCD-Schema Bewertungen
- Medizinische Besonderheiten (z.B. ASS-Allergie, Antikoagulation)

**Ausnahme gemaess Art. 9(2)(c):** Die Verarbeitung ist erforderlich zum Schutz lebenswichtiger Interessen der betroffenen Person, wenn diese physisch nicht in der Lage ist, eine Einwilligung zu erteilen.

**Zusaetzlich Art. 9(2)(h):** Die Verarbeitung ist fuer Zwecke der Gesundheitsversorgung erforderlich und erfolgt durch Fachpersonal, das der Schweigepflicht unterliegt.

---

## 4. Technische und Organisatorische Massnahmen (TOM)

### 4.1 In OpMan_GPT implementierte Massnahmen

| Massnahme | Implementierung | Status |
|-----------|----------------|--------|
| **Feld-Verschluesselung** | Fernet (AES-128-CBC) fuer Patientennamen | Implementiert |
| **RBAC** | 7 Rollen mit Hierarchie (admin bis beobachter) | Implementiert |
| **MFA** | TOTP (pyotp) fuer alle Benutzer | Implementiert |
| **Brute-Force-Schutz** | Account-Sperrung nach 5 Fehlversuchen (15 Min) | Implementiert |
| **Session-Management** | Secure Cookies, CSRF, Session-Limiting | Implementiert |
| **Audit-Logging** | Hash-Chain (SHA-256), alle Aktionen protokolliert | Implementiert |
| **Anomalie-Erkennung** | Neue IP, Geschaeftszeiten, Fehlversuche | Implementiert |
| **Breach-Erkennung** | Automatische Pruefung auf Datenpannen-Indikatoren | Implementiert |
| **Pseudonymisierung** | Patientennamen durch Pseudonyme ersetzbar | Implementiert |
| **Recht auf Loeschung** | Anonymisierung einzelner Faelle (Art. 17) | Implementiert |
| **Datenportabilitaet** | JSON-Export (Art. 20) | Implementiert |
| **Auto-Cleanup** | Automatische Anonymisierung nach Aufbewahrungsfrist | Implementiert |
| **Rate Limiting** | Flask-Limiter gegen DoS | Implementiert |
| **Passwort-Hashing** | bcrypt mit Salt | Implementiert |
| **HTTPS** | TLS mit selbstsigniertem Zertifikat | Implementiert |
| **Einwilligungsverwaltung** | Consent-Records mit Widerruf | Implementiert |
| **Datenminimierungsbericht** | Automatischer Report aller Datenfelder | Implementiert |

### 4.2 Zusaetzlich empfohlene Massnahmen

| Massnahme | Prioritaet | Status |
|-----------|-----------|--------|
| Festplattenverschluesselung (LUKS) | Hoch | [ ] Ausstehend |
| Externes Backup-System (verschluesselt) | Hoch | [ ] Ausstehend |
| Netzwerk-Segmentierung | Mittel | [ ] Ausstehend |
| Host-basiertes IDS (OSSEC/Wazuh) | Mittel | [ ] Ausstehend |
| Hardware Security Module (HSM) | Niedrig | [ ] Evaluierung |
| Zertifikat von oeffentlicher CA | Niedrig | [ ] Optional |

---

## 5. Restrisiko-Bewertung

### 5.1 Restrisiken nach Massnahmen

| Nr. | Risiko | Risiko vorher | Massnahmen | Restrisiko | Akzeptabel? |
|-----|--------|--------------|-----------|-----------|-------------|
| R1 | Unbefugter Zugriff | 8 (Hoch) | RBAC, MFA, Verschluesselung | 3 (Niedrig) | Ja |
| R2 | Datenverlust | 8 (Hoch) | Backup, BCM | 4 (Mittel) | Ja (mit Backup) |
| R3 | Log-Manipulation | 4 (Mittel) | Hash-Chain | 2 (Niedrig) | Ja |
| R4 | GPS-Ueberwachung | 6 (Mittel) | RBAC, Auto-Loeschung | 3 (Niedrig) | Ja |
| R5 | Brute-Force | 9 (Hoch) | Sperrung, Limiting | 3 (Niedrig) | Ja |
| R6 | Insider-Missbrauch | 8 (Hoch) | Audit, Breach-Check | 4 (Mittel) | Ja (Monitoring) |
| R7 | Schluesselverlust | 4 (Mittel) | Schluessel-Backup | 2 (Niedrig) | Ja |
| R8 | Session-Hijacking | 6 (Mittel) | Secure Cookies, CSRF | 3 (Niedrig) | Ja |
| R9 | Physischer Zugriff | 4 (Mittel) | Zutrittskontrolle | 2 (Niedrig) | Ja |
| R10 | Uebermaessige Speicherung | 6 (Mittel) | Auto-Cleanup | 2 (Niedrig) | Ja |

### 5.2 Gesamtbewertung Restrisiko

Das Gesamtrestrisiko wird nach Umsetzung aller Massnahmen als **AKZEPTABEL** bewertet.

**Begruendung:**
- Alle hohen Risiken wurden durch technische Massnahmen auf ein vertretbares Niveau reduziert
- Die implementierten Massnahmen entsprechen dem Stand der Technik
- Der lokale Betrieb (kein Cloud-Dienst) reduziert Risiken erheblich
- Gesundheitsdaten sind verschluesselt und zugangsgeschuetzt

---

## 6. Konsultation der Aufsichtsbehoerde (Art. 36 DSGVO)

### 6.1 Notwendigkeit der Konsultation

Eine vorherige Konsultation der Aufsichtsbehoerde ist erforderlich, wenn die DSFA ergibt, dass die Verarbeitung ein hohes Risiko birgt und der Verantwortliche keine ausreichenden Massnahmen zur Eindaemmung des Risikos trifft.

**Bewertung:** Die implementierten Massnahmen reduzieren alle identifizierten Risiken auf ein akzeptables Niveau. Eine Konsultation der Aufsichtsbehoerde ist daher **nicht erforderlich**.

### 6.2 Falls Konsultation erforderlich wird

Zustaendige Aufsichtsbehoerde:
- **Deutschland:** Landesdatenschutzbehoerde des Bundeslandes
- **Oesterreich:** Oesterreichische Datenschutzbehoerde (DSB)

---

## 7. Stellungnahme des Datenschutzbeauftragten

Der Datenschutzbeauftragte wurde in die Erstellung dieser DSFA einbezogen (Art. 35 Abs. 2 DSGVO).

**Stellungnahme:**

> [Hier Stellungnahme des DSB einfuegen]
>
> Datum: ___.___.______
> Unterschrift DSB: _________________________

---

## 8. Ueberpruefung und Aktualisierung

Diese DSFA wird ueberprueft:
- **Regelmaessig:** Mindestens jaehrlich
- **Anlassbezogen:** Bei wesentlichen Aenderungen der Verarbeitung
- **Naechste Ueberpruefung:** ___.___.______

---

## 9. Freigabe

| Rolle | Name | Datum | Unterschrift |
|-------|------|-------|-------------|
| Verantwortlicher | | | |
| Datenschutzbeauftragter | | | |
| IT-Sicherheitsbeauftragter | | | |
| Geschaeftsfuehrung | | | |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
