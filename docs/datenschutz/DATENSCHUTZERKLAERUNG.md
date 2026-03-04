# Datenschutzerklaerung -- OpMan_GPT

**Dokument:** Datenschutzerklaerung gemaess Art. 13, 14 DSGVO
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026

---

## 1. Verantwortlicher

Verantwortlicher im Sinne der Datenschutz-Grundverordnung (DSGVO) ist:

**[Name der Organisation / des Rettungsdienstes]**
[Strasse und Hausnummer]
[PLZ Ort]
Telefon: [+49 xxx xxxxxxx]
E-Mail: [kontakt@organisation.de]

## 2. Datenschutzbeauftragter

Unseren Datenschutzbeauftragten erreichen Sie unter:

[Name des DSB]
E-Mail: [datenschutz@organisation.de]
Telefon: [+49 xxx xxxxxxx]

---

## 3. Uebersicht der Datenverarbeitungen

### 3.1 Patientendaten

| Aspekt | Details |
|--------|---------|
| **Daten** | Name, Alarmierungsname, Alter, Geschlecht, Vitalparameter, Besonderheiten (Allergien, Vorerkrankungen), ABCD-Schema |
| **Zweck** | Dokumentation und Koordination der medizinischen Notfallversorgung |
| **Rechtsgrundlage** | Art. 6(1)(e) DSGVO (Wahrnehmung oeffentlicher Aufgabe) i.V.m. Rettungsdienstgesetz; Art. 9(2)(c) DSGVO (Schutz lebenswichtiger Interessen); Art. 9(2)(h) DSGVO (Gesundheitsversorgung) |
| **Speicherdauer** | 10 Jahre (gemaess Rettungsdienstgesetz); Uebungsdaten: 1 Jahr |
| **Empfaenger** | Leitstellenpersonal, Rettungsteams, aufnehmende Kliniken, Aerztlicher Leiter |
| **Besonderheit** | Gesundheitsdaten gemaess Art. 9 DSGVO. Verschluesselte Speicherung (Fernet/AES). |

### 3.2 Einsatzdaten

| Aspekt | Details |
|--------|---------|
| **Daten** | Einsatztitel, Beschreibung, Prioritaet, Status, Standort (GPS-Koordinaten), Zeitstempel |
| **Zweck** | Koordination und Dokumentation von Rettungseinsaetzen |
| **Rechtsgrundlage** | Art. 6(1)(e) DSGVO i.V.m. Rettungsdienstgesetz |
| **Speicherdauer** | 10 Jahre |
| **Empfaenger** | Leitstellenpersonal, Einsatzkraefte |

### 3.3 GPS-Standortdaten

| Aspekt | Details |
|--------|---------|
| **Daten** | GPS-Koordinaten (Laengen-/Breitengrad) der Einsatzteams, Zeitstempel |
| **Zweck** | Optimale Disposition der naechstgelegenen Rettungsteams, Einsatzkoordination |
| **Rechtsgrundlage** | Art. 6(1)(f) DSGVO (berechtigtes Interesse: lebensrettende Notfallversorgung) |
| **Speicherdauer** | 90 Tage |
| **Empfaenger** | Leitstellenpersonal (Disponenten, Schichtleiter) |
| **Hinweis** | GPS-Tracking erfolgt nur waehrend der aktiven Schicht ueber die mobile EVT-App. Die Standorterfassung kann vom Benutzer im Browser deaktiviert werden. |

### 3.4 Funkprotokoll

| Aspekt | Details |
|--------|---------|
| **Daten** | Teamname, Rufname, Nachrichteninhalt, Statuswechsel, Zeitstempel |
| **Zweck** | Gesetzlich vorgeschriebene Dokumentation der Funkkommunikation |
| **Rechtsgrundlage** | Art. 6(1)(c) DSGVO (rechtliche Verpflichtung gemaess Rettungsdienstgesetz) |
| **Speicherdauer** | 1 Jahr |
| **Empfaenger** | Leitstellenpersonal |

### 3.5 Benutzerdaten

| Aspekt | Details |
|--------|---------|
| **Daten** | Benutzername, Passwort (gehasht mit bcrypt), Rolle, Anzeigename, MFA-Konfiguration (TOTP-Secret), Letzter Login, Fehlversuche, Sperrungsstatus |
| **Zweck** | Authentifizierung, Autorisierung, Zugangssteuerung |
| **Rechtsgrundlage** | Art. 6(1)(b) DSGVO (Vertragserfullung / Beschaeftigungsverhaeltnis) |
| **Speicherdauer** | Dauer des Benutzerkontos plus 3 Jahre (Nachweispflicht) |
| **Empfaenger** | Systemadministratoren |

### 3.6 Audit-Protokolle

| Aspekt | Details |
|--------|---------|
| **Daten** | Zeitstempel, Benutzer-ID, Benutzername, Aktion, betroffene Ressource, Details, IP-Adresse, User-Agent, Integritaets-Hash |
| **Zweck** | Revisionssichere Protokollierung, Compliance (NIS2/BSIG), IT-Sicherheit, Forensik |
| **Rechtsgrundlage** | Art. 6(1)(c) DSGVO (rechtliche Verpflichtung: BSIG, NIS2); Art. 6(1)(f) DSGVO (berechtigtes Interesse: IT-Sicherheit) |
| **Speicherdauer** | 3 Jahre |
| **Empfaenger** | Administratoren, IS-Beauftragter, Datenschutzbeauftragter |

### 3.7 Web-Push-Abonnements

| Aspekt | Details |
|--------|---------|
| **Daten** | Push-Endpoint-URL, kryptografische Schluessel (p256dh, auth), EVT-Name |
| **Zweck** | Einsatzalarmierung der Rettungsteams per Push-Benachrichtigung |
| **Rechtsgrundlage** | Art. 6(1)(f) DSGVO (berechtigtes Interesse: zeitkritische Alarmierung) |
| **Speicherdauer** | Bis zur Abmeldung des Geraetes |
| **Empfaenger** | Push-Dienst des Browser-Herstellers (technisch unvermeidbar) |

---

## 4. Besondere Kategorien personenbezogener Daten (Art. 9 DSGVO)

OpMan_GPT verarbeitet **Gesundheitsdaten** (besondere Kategorie gemaess Art. 9 DSGVO). Dies umfasst:

- Vitalparameter (Puls, Blutdruck, SpO2, etc.)
- Medizinische Besonderheiten (Allergien, Vorerkrankungen)
- ABCD-Schema-Bewertungen
- Alter und Geschlecht im medizinischen Kontext

**Ausnahmeregelungen:**

- **Art. 9(2)(c) DSGVO:** Die Verarbeitung ist zum Schutz lebenswichtiger Interessen der betroffenen Person erforderlich, und die Person ist physisch oder rechtlich ausser Stande, ihre Einwilligung zu geben (Notfallsituation).
- **Art. 9(2)(h) DSGVO:** Die Verarbeitung ist fuer Zwecke der Gesundheitsversorgung auf Grundlage des Rettungsdienstgesetzes erforderlich und erfolgt durch Fachpersonal, das der Schweigepflicht unterliegt.

---

## 5. Rechte der betroffenen Personen

Als betroffene Person haben Sie folgende Rechte:

### 5.1 Auskunftsrecht (Art. 15 DSGVO)

Sie haben das Recht, Auskunft ueber die von uns verarbeiteten personenbezogenen Daten zu verlangen. Dies umfasst den Zweck der Verarbeitung, die Kategorien der Daten, die Empfaenger und die Speicherdauer.

### 5.2 Recht auf Berichtigung (Art. 16 DSGVO)

Sie haben das Recht, die Berichtigung unrichtiger Daten zu verlangen.

### 5.3 Recht auf Loeschung (Art. 17 DSGVO)

Sie haben das Recht, die Loeschung Ihrer Daten zu verlangen, sofern keine gesetzlichen Aufbewahrungspflichten entgegenstehen. OpMan_GPT unterstuetzt die Anonymisierung von Falldaten ueber die DSGVO-Funktionalitaet.

**Einschraenkung:** Einsatzdokumentationen unterliegen gesetzlichen Aufbewahrungsfristen (Rettungsdienstgesetz). In diesen Faellen erfolgt anstelle der Loeschung eine Anonymisierung der personenbezogenen Daten.

### 5.4 Recht auf Einschraenkung der Verarbeitung (Art. 18 DSGVO)

Sie haben das Recht, die Einschraenkung der Verarbeitung zu verlangen, z.B. wenn die Richtigkeit der Daten bestritten wird.

### 5.5 Recht auf Datenportabilitaet (Art. 20 DSGVO)

Sie haben das Recht, Ihre Daten in einem strukturierten, gaengigen und maschinenlesbaren Format (JSON) zu erhalten. OpMan_GPT bietet eine Export-Funktion gemaess Art. 20 DSGVO.

### 5.6 Widerspruchsrecht (Art. 21 DSGVO)

Sie haben das Recht, der Verarbeitung Ihrer Daten zu widersprechen, sofern die Verarbeitung auf Art. 6(1)(e) oder (f) DSGVO beruht. Bei der GPS-Standorterfassung koennen Sie das Tracking im Browser deaktivieren.

### 5.7 Recht auf Widerruf der Einwilligung (Art. 7(3) DSGVO)

Sofern eine Verarbeitung auf Einwilligung beruht, koennen Sie diese jederzeit widerrufen. OpMan_GPT verfuegt ueber eine Einwilligungsverwaltung mit Widerruf-Funktion.

### 5.8 Beschwerderecht (Art. 77 DSGVO)

Sie haben das Recht, sich bei einer Datenschutz-Aufsichtsbehoerde zu beschweren:

- **Deutschland:** Zustaendige Landesdatenschutzbehoerde
- **Oesterreich:** Oesterreichische Datenschutzbehoerde (DSB), Barichgasse 40-42, 1030 Wien

---

## 6. Technische und Organisatorische Massnahmen

Zum Schutz Ihrer Daten setzen wir folgende Massnahmen ein:

- **Verschluesselung:** Patientennamen werden mit Fernet (AES-128-CBC) verschluesselt gespeichert. Die Uebertragung erfolgt ueber HTTPS (TLS).
- **Zugangssteuerung:** Rollenbasierte Zugriffskontrolle (RBAC) mit 7 definierten Rollen.
- **Authentifizierung:** bcrypt-Passwort-Hashing, optionale Multi-Faktor-Authentifizierung (TOTP).
- **Brute-Force-Schutz:** Automatische Account-Sperrung nach 5 fehlgeschlagenen Anmeldeversuchen.
- **Pseudonymisierung:** Patientendaten koennen pseudonymisiert werden.
- **Audit-Trail:** Revisionssichere Protokollierung aller Zugriffe mit Hash-Kette (SHA-256).
- **Datensparsamkeit:** Automatische Anonymisierung nach Ablauf der Aufbewahrungsfrist.
- **Lokaler Betrieb:** Alle Daten bleiben im lokalen Netzwerk. Kein Cloud-Dienst, keine externe Datenspeicherung.

---

## 7. Kein Drittlandtransfer

OpMan_GPT wird vollstaendig lokal im LAN betrieben. Personenbezogene Daten werden nicht in Drittlaender (ausserhalb EU/EWR) uebertragen.

**Ausnahme:** Bei Nutzung der Web-Push-Funktion koennen Push-Endpunkte ueber Dienste der Browser-Hersteller (z.B. Google FCM) geleitet werden. Die Push-Nachrichten selbst sind Ende-zu-Ende verschluesselt (VAPID/Web Push Protocol).

---

## 8. Automatisierte Entscheidungsfindung

Es findet keine automatisierte Entscheidungsfindung im Sinne von Art. 22 DSGVO statt. Alle Disposition- und Einsatzentscheidungen werden von menschlichen Disponenten getroffen.

---

## 9. Aenderung der Datenschutzerklaerung

Diese Datenschutzerklaerung wird bei Bedarf aktualisiert. Die aktuelle Fassung ist in der Anwendung unter dem Menue "Datenschutz" abrufbar.

Stand: 04.03.2026

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
