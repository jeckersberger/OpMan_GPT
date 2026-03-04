# KRITIS-Massnahmen und Sicherheitsanforderungen

**Dokument:** KRITIS-Massnahmenkatalog fuer OpMan_GPT
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich
**Rechtsgrundlage:** ss 8a BSIG, NIS2UmsuCG, BSI-KritisV

---

## 1. Einleitung

Einsatzleitstellen und Rettungsdienste gehoeren zum KRITIS-Sektor "Gesundheit". Der Betrieb von OpMan_GPT als Einsatzleitsoftware erfordert die Umsetzung von Massnahmen nach dem Stand der Technik gemaess ss 8a BSIG sowie dem NIS2UmsuCG.

---

## 2. ISMS-Implementierungsfahrplan

### Phase 1: Initiierung (Monat 1-2)

| Massnahme | Verantwortlich | Status |
|-----------|----------------|--------|
| Management-Commitment einholen | Geschaeftsfuehrung | [ ] |
| IS-Beauftragten benennen | Geschaeftsfuehrung | [ ] |
| Geltungsbereich (Scope) definieren | IS-Beauftragter | [ ] |
| IS-Leitlinie erstellen | IS-Beauftragter | [ ] |
| Budget und Ressourcen planen | Geschaeftsfuehrung | [ ] |
| Projektplan erstellen | IS-Beauftragter | [ ] |

### Phase 2: Bestandsaufnahme (Monat 2-4)

| Massnahme | Verantwortlich | Status |
|-----------|----------------|--------|
| Asset-Inventar erstellen | IT-Leitung | [ ] |
| Geschaeftsprozesse identifizieren | Fachbereich | [ ] |
| Schutzbedarfsfeststellung durchfuehren | IS-Beauftragter | [ ] |
| IT-Strukturanalyse (BSI IT-Grundschutz) | IT-Leitung | [ ] |
| Bedrohungsanalyse durchfuehren | IS-Beauftragter | [ ] |
| Risikoanalyse dokumentieren | IS-Beauftragter | [ ] |

### Phase 3: Umsetzung (Monat 4-9)

| Massnahme | Verantwortlich | Status |
|-----------|----------------|--------|
| Sicherheitsmassnahmen ableiten | IS-Beauftragter | [ ] |
| Technische Massnahmen umsetzen | IT-Leitung | [ ] |
| Organisatorische Massnahmen umsetzen | IS-Beauftragter | [ ] |
| Mitarbeiterschulungen durchfuehren | IS-Beauftragter | [ ] |
| Dokumentation vervollstaendigen | IS-Beauftragter | [ ] |
| Notfallmanagement aufbauen | IS-Beauftragter | [ ] |

### Phase 4: Betrieb und Verbesserung (fortlaufend)

| Massnahme | Verantwortlich | Turnus |
|-----------|----------------|--------|
| Interne Audits | IS-Beauftragter | Jaehrlich |
| Management-Review | Geschaeftsfuehrung | Jaehrlich |
| Risikobewertung aktualisieren | IS-Beauftragter | Jaehrlich |
| Wirksamkeitspruefung | IS-Beauftragter | Quartalsweise |
| Sicherheitsaudit (BSI) | Externer Pruefer | Alle 2 Jahre |

---

## 3. Biennales Sicherheitsaudit (ss 39 BSIG)

### 3.1 Anforderungen

- **Turnus:** Alle 2 Jahre (erstmals innerhalb von 2 Jahren nach Registrierung)
- **Pruefer:** BSI-anerkannte Pruefstelle oder qualifizierter Auditor
- **Umfang:** Umsetzung der Anforderungen nach ss 30 BSIG
- **Ergebnis:** Pruefbericht mit Maengelliste an BSI uebermitteln

### 3.2 Audit-Vorbereitung Checkliste

- [ ] Alle ISMS-Dokumente aktuell und vollstaendig
- [ ] Risikoanalyse aktuell (nicht aelter als 12 Monate)
- [ ] Technische Massnahmen dokumentiert und nachweisbar
- [ ] Schulungsnachweise vorhanden
- [ ] Incident-Log gefuehrt
- [ ] Penetrationstest-Bericht vorhanden (nicht aelter als 12 Monate)
- [ ] BCM-Plan getestet
- [ ] Lieferantenbewertungen durchgefuehrt
- [ ] Audit-Trail / Audit-Log integer (Hash-Chain in OpMan_GPT)

### 3.3 Typischer Audit-Ablauf

```
1. Dokumentenpruefung (Remote, 1-2 Tage)
   - ISMS-Dokumentation
   - Risikoanalyse
   - Massnahmenplan

2. Vor-Ort-Pruefung (2-3 Tage)
   - Interviews mit Verantwortlichen
   - Technische Pruefung der Systeme
   - Stichproben der Prozesse
   - Pruefung der physischen Sicherheit

3. Berichtserstellung (1-2 Wochen)
   - Feststellungen und Empfehlungen
   - Maengelliste (kritisch/hoch/mittel/niedrig)
   - Nachweisfrist fuer Maengelbeseitigung

4. Nachpruefung (bei kritischen Maengeln)
   - Nachweis der Maengelbeseitigung
   - Ggf. erneute Vor-Ort-Pruefung
```

---

## 4. Angriffserkennung (IDS/IPS, SIEM)

### 4.1 Anforderungen (ss 30 Abs. 1 Nr. 2 BSIG)

Systeme zur Angriffserkennung muessen:
- Geeignete technische Werkzeuge einsetzen
- Automatisiert und kontinuierlich Bedrohungen erkennen
- Bedrohungsinformationen (Threat Intelligence) nutzen
- Vorfaelle korrelieren und priorisieren

### 4.2 Empfohlene Architektur fuer OpMan_GPT

```
                    +------------------+
                    |   SIEM-System    |
                    | (z.B. Wazuh,    |
                    |  ELK Stack)     |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------+----+ +------+------+ +-----+-------+
     | Netzwerk-IDS| | Host-IDS   | | Application |
     | (Suricata)  | | (OSSEC/    | | Logging     |
     |             | |  Wazuh)    | | (OpMan_GPT) |
     +-------------+ +------------+ +-------------+
                                          |
                                   +------+------+
                                   | Audit-Log   |
                                   | (Hash-Chain) |
                                   | AuditLog DB  |
                                   +-------------+
```

### 4.3 Umsetzungsplan

| Komponente | Beschreibung | Prioritaet | Status |
|-----------|-------------|-----------|--------|
| Application Logging | Audit-Log in OpMan_GPT (bereits implementiert) | Hoch | [x] Umgesetzt |
| Anomalie-Erkennung | Login-Anomalien in OpMan_GPT (implementiert) | Hoch | [x] Umgesetzt |
| Breach-Erkennung | DSGVO Breach-Check in OpMan_GPT (implementiert) | Hoch | [x] Umgesetzt |
| Host-basiertes IDS | OSSEC / Wazuh Agent auf Server | Hoch | [ ] Offen |
| Netzwerk-IDS | Suricata an Netzwerk-Perimeter | Mittel | [ ] Offen |
| SIEM-Integration | Zentrales Log-Management (ELK/Wazuh) | Mittel | [ ] Offen |
| Threat Intelligence | MISP / BSI-Warnmeldungen einbinden | Niedrig | [ ] Offen |

### 4.4 In OpMan_GPT bereits implementierte Erkennungsmechanismen

| Mechanismus | Beschreibung | Modul |
|------------|-------------|-------|
| Brute-Force-Erkennung | Account-Sperrung nach 5 Fehlversuchen | auth.py |
| Anomalie-Erkennung | Neue IP, ausserhalb Geschaeftszeiten, mehrfache Fehlversuche | auth.py |
| Breach-Indikator-Pruefung | Massenexporte, unaut. Zugriffe, Massenloeschungen | dsgvo.py |
| Hash-Chain Audit-Log | Manipulationserkennung durch verkettete SHA-256-Hashes | auth.py |
| API-Zugriffs-Logging | Alle API-Aufrufe werden protokolliert | auth.py |
| Session-Limiting | Nur eine aktive Session pro Benutzer | auth.py |
| Rate Limiting | Flask-Limiter gegen DoS/Brute-Force | app.py |

---

## 5. Resilienz-Plan

### 5.1 Schutzziele fuer OpMan_GPT

| Schutzziel | Anforderung | Massnahme |
|-----------|-------------|-----------|
| Verfuegbarkeit | 99,9% (RTO: 15 Min) | Redundanz, Backup, Notbetrieb |
| Integritaet | Manipulationsschutz | Hash-Chain Audit, DB-Integritaet |
| Vertraulichkeit | Schutz pers. Daten | Verschluesselung, RBAC, MFA |
| Authentizitaet | Identitaetssicherung | bcrypt, TOTP, Session-Mgmt |
| Nicht-Abstreitbarkeit | Nachvollziehbarkeit | Audit-Log mit Hash-Chain |

### 5.2 Resilienz-Massnahmen

#### Praeventiv (vor einem Vorfall)

- [ ] Regelmaessige Backups (taeglich, inkrementell)
- [ ] Backup-Verschluesselung
- [ ] Backup-Tests (monatlich)
- [ ] Redundante Infrastruktur (Datenbank, Netzwerk)
- [ ] Patch-Management (kritische Patches: 24h, hoch: 7 Tage)
- [ ] Haertung des Betriebssystems
- [ ] Netzwerk-Segmentierung
- [ ] Firewall-Regeln (Whitelist-Ansatz)

#### Reaktiv (waehrend eines Vorfalls)

- [ ] Incident-Response-Plan aktivieren
- [ ] Isolierung betroffener Systeme
- [ ] Forensische Sicherung
- [ ] Kommunikation an Stakeholder
- [ ] Notbetrieb einleiten (papierbasiert)
- [ ] BSI-Meldung (24h Fruehwarnung)

#### Wiederherstellung (nach einem Vorfall)

- [ ] System aus Backup wiederherstellen
- [ ] Integritaetspruefung durchfuehren
- [ ] Schrittweise Wiederinbetriebnahme
- [ ] Monitoring verstaerken
- [ ] Lessons Learned durchfuehren
- [ ] Massnahmen aktualisieren

---

## 6. Zugriffsberechtigungsmatrix

### 6.1 OpMan_GPT Rollenmodell

| Rolle | Hierarchie | Beschreibung |
|-------|-----------|-------------|
| admin | 100 | Systemkonfiguration, Benutzerverwaltung, voller Zugriff |
| schichtleiter | 80 | Erweiterte Rechte, Aufsicht, Audit-Log-Einsicht |
| disponent | 60 | Einsatzverwaltung, Alarmierung, Disposition |
| aerztlicher_leiter | 50 | Medizinische Qualitaetsdaten |
| datenschutz | 50 | Audit-Logs, DSGVO-Funktionen, Verarbeitungsverzeichnisse |
| evt_operator | 30 | Eigener Status, eigene Einsaetze, GPS |
| beobachter | 10 | Nur Lesezugriff auf Lagekarte |

### 6.2 Berechtigungsmatrix

| Funktion | admin | schichtleiter | disponent | aerztl_leiter | datenschutz | evt_operator | beobachter |
|----------|-------|--------------|-----------|--------------|-------------|-------------|-----------|
| Benutzerverwaltung | X | - | - | - | - | - | - |
| Systemkonfiguration | X | - | - | - | - | - | - |
| Einsaetze erstellen | X | X | X | - | - | - | - |
| Einsaetze zuweisen | X | X | X | - | - | - | - |
| Trupps verwalten | X | X | X | - | - | - | - |
| Funkstatus aendern | X | X | X | - | - | X | - |
| GPS-Position senden | X | X | X | - | - | X | - |
| Falldokumentation | X | X | X | X | - | X | - |
| Funkprotokoll | X | X | X | - | - | - | - |
| Lagekarte (lesen) | X | X | X | X | X | X | X |
| Audit-Log einsehen | X | X | - | - | X | - | - |
| DSGVO-Dashboard | X | X | - | - | X | - | - |
| Datenexport (DSGVO) | X | - | - | - | X | - | - |
| Datenlöschung (DSGVO) | X | - | - | - | X | - | - |
| Pseudonymisierung | X | - | - | - | X | - | - |
| Break-Glass Zugriff | X | - | - | - | - | - | - |

### 6.3 Zugriffsueberprufung (Access Review)

- **Turnus:** Alle 90 Tage (in OpMan_GPT implementiert: `/api/admin/access-review`)
- **Verantwortlich:** Administrator / IS-Beauftragter
- **Dokumentation:** Ergebnis wird als Audit-Log-Eintrag gespeichert
- **Massnahmen bei Auffaelligkeiten:**
  - Nicht mehr benoetigte Accounts deaktivieren
  - Rollen ueberpruefen und ggf. anpassen
  - Inaktive Accounts (> 90 Tage ohne Login) sperren

---

## 7. Physische Sicherheit (Leitstellenraum)

| Massnahme | Beschreibung | Status |
|-----------|-------------|--------|
| Zutrittskontrolle | Elektronisches Schliessystem, Protokollierung | [ ] |
| Videoüberwachung | Eingangsbereich und Serverraum | [ ] |
| USV | Unterbrechungsfreie Stromversorgung (min. 30 Min) | [ ] |
| Klimatisierung | Temperaturueberwachung Serverraum | [ ] |
| Brandschutz | Brandmeldeanlage, Loeschanlage | [ ] |
| Einbruchmeldeanlage | Aufschaltung auf Wachdienst | [ ] |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
