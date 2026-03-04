# Business Continuity Management Plan (BCM)

**Dokument:** BCM-Plan gemaess BSI-Standard 200-4
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern -- Vertraulich

---

## 1. Zweck

Dieser BCM-Plan stellt sicher, dass der Betrieb der Einsatzleitsoftware OpMan_GPT auch bei Stoerungen, Ausfaellen oder Katastrophen aufrechterhalten oder zeitnah wiederhergestellt werden kann. Als KRITIS-relevante Software im Rettungsdienst hat die Verfuegbarkeit direkte Auswirkungen auf die Patientenversorgung.

---

## 2. Business Impact Analyse (BIA)

### 2.1 Kritische Geschaeftsprozesse

| Prozess | Kritikalitaet | Max. tolerierbare Ausfallzeit (MTPD) | RTO | RPO |
|---------|-------------|-------------------------------------|-----|-----|
| Einsatzdisposition | **Sehr hoch** | 15 Minuten | 15 Min | 0 Min |
| Funkstatus-Tracking | **Sehr hoch** | 15 Minuten | 15 Min | 5 Min |
| GPS-Tracking Teams | Hoch | 30 Minuten | 30 Min | 5 Min |
| Alarmierung (Push) | **Sehr hoch** | 5 Minuten | 5 Min | 0 Min |
| Falldokumentation | Hoch | 1 Stunde | 1 Std | 15 Min |
| Funkprotokoll | Mittel | 4 Stunden | 4 Std | 30 Min |
| Benutzerverwaltung | Niedrig | 24 Stunden | 24 Std | 1 Std |
| DSGVO-Dashboard | Niedrig | 48 Stunden | 48 Std | 24 Std |
| Audit-Logging | Hoch | 30 Minuten | 30 Min | 0 Min |
| Monitoring | Mittel | 1 Stunde | 1 Std | 15 Min |

**Legende:**
- MTPD: Maximum Tolerable Period of Disruption
- RTO: Recovery Time Objective (Wiederanlaufzeit)
- RPO: Recovery Point Objective (max. akzeptabler Datenverlust)

### 2.2 Abhaengigkeiten

```
OpMan_GPT
  |
  +-- Server-Hardware
  |     +-- Stromversorgung (USV, NEA)
  |     +-- Netzwerk (LAN-Switch, Router)
  |     +-- Festplatte / SSD
  |
  +-- Betriebssystem (Linux)
  |     +-- Python 3 Runtime
  |     +-- SQLite / PostgreSQL
  |
  +-- Netzwerk-Infrastruktur
  |     +-- LAN (Ethernet)
  |     +-- WLAN (fuer mobile EVT-Geraete)
  |     +-- Firewall
  |
  +-- Client-Geraete
  |     +-- Leitstellenarbeitsplaetze (Browser)
  |     +-- Mobile EVT-Geraete (Smartphones)
  |
  +-- Externe Dienste (optional)
        +-- OpenStreetMap (Kartenkacheln)
        +-- Browser-Push-Dienste
```

### 2.3 Schadenszenarien

| Szenario | Auswirkung | Wahrscheinlichkeit | Risiko |
|----------|-----------|-------------------|--------|
| Serverausfall (Hardware) | Totalausfall OpMan_GPT | Niedrig | Hoch |
| Stromausfall | Totalausfall aller Systeme | Mittel | Sehr hoch |
| Netzwerkausfall (LAN) | Kein Zugriff auf OpMan_GPT | Niedrig | Hoch |
| Datenbankkorruption | Datenverlust, Systemfehler | Sehr niedrig | Hoch |
| Ransomware | Verschluesselung aller Daten | Niedrig | Sehr hoch |
| Fehlkonfiguration | Teilausfall, Fehlfunktionen | Mittel | Mittel |
| Softwarefehler (Bug) | Funktionseinschraenkung | Mittel | Mittel |
| DDoS-Angriff | Performance-Degradation | Niedrig | Mittel |
| Personalausfall (IT) | Verzoegerte Fehlerbehebung | Mittel | Mittel |

---

## 3. Kontinuitaetsstrategien

### 3.1 Praeventive Massnahmen (vor Stoerung)

| Massnahme | Beschreibung | Verantwortlich | Status |
|-----------|-------------|----------------|--------|
| Taegl. Backup | SQLite-DB und encryption.key sichern | IT-Admin | [ ] |
| Backup-Verschluesselung | Backups mit AES-256 verschluesseln | IT-Admin | [ ] |
| Backup-Offsite | Kopie an getrenntem Standort | IT-Admin | [ ] |
| USV | Min. 30 Min Ueberbrueckung | Haustechnik | [ ] |
| Netzersatzanlage | Diesel-Generator fuer Dauerbetrieb | Haustechnik | [ ] |
| Redundanter Server | Standby-Server mit Konfiguration | IT-Admin | [ ] |
| RAID-System | Festplattenspiegelung | IT-Admin | [ ] |
| Netzwerk-Redundanz | Redundante Switches, Uplinks | IT-Admin | [ ] |
| Dokumentation | Aktuelles Runbook und Architektur | IT-Admin | [ ] |
| Schulung | Personal in Notverfahren geschult | Leitstellenleitung | [ ] |
| Notfall-Vordrucke | Papierbasierte Formulare bereit | Leitstellenleitung | [ ] |

### 3.2 Reaktive Massnahmen (waehrend Stoerung)

#### Szenario: Serverausfall

| Schritt | Massnahme | Verantwortlich | Dauer |
|---------|-----------|----------------|-------|
| 1 | Notbetrieb einleiten (Papier/Whiteboard) | Schichtleiter | Sofort |
| 2 | IT-Bereitschaft alarmieren | Schichtleiter | 5 Min |
| 3 | Hardware-Diagnose | IT-Admin | 15 Min |
| 4 | Standby-Server aktivieren (falls vorhanden) | IT-Admin | 15 Min |
| 5 | Oder: Backup auf Ersatzhardware einspielen | IT-Admin | 30-60 Min |
| 6 | System testen | IT-Admin | 10 Min |
| 7 | Normalbetrieb wiederaufnehmen | Schichtleiter | 5 Min |
| 8 | Nacherfassung aus Papierprotokollen | Disponenten | Nach Bedarf |

#### Szenario: Stromausfall

| Schritt | Massnahme | Verantwortlich | Dauer |
|---------|-----------|----------------|-------|
| 1 | USV uebernimmt automatisch | Automatisch | Sofort |
| 2 | Netzersatzanlage starten (falls > 15 Min) | Haustechnik | 5 Min |
| 3 | Nicht-kritische Systeme herunterfahren | IT-Admin | 10 Min |
| 4 | Batteriestatus ueberwachen | IT-Admin | Laufend |
| 5 | Bei langem Ausfall: Notbetrieb | Schichtleiter | 30 Min |

#### Szenario: Ransomware

| Schritt | Massnahme | Verantwortlich | Dauer |
|---------|-----------|----------------|-------|
| 1 | Sofort Netzwerk trennen | IT-Admin | Sofort |
| 2 | Notbetrieb einleiten | Schichtleiter | 5 Min |
| 3 | Forensische Sicherung | IT-Admin / Forensik | 1-4 Std |
| 4 | BSI/Polizei informieren | ISB / GF | 1 Std |
| 5 | Sauberes System aus Backup aufsetzen | IT-Admin | 2-4 Std |
| 6 | Alle Passwoerter zuruecksetzen | IT-Admin | 1 Std |
| 7 | Schrittweise Wiederinbetriebnahme | IT-Admin | 1-2 Std |

### 3.3 Wiederherstellungsmassnahmen (nach Stoerung)

| Massnahme | Beschreibung | Verantwortlich |
|-----------|-------------|----------------|
| Integritaetspruefung | Datenbank und Audit-Log-Hash-Chain pruefen | IT-Admin |
| Funktionstest | Alle kritischen Funktionen testen | IT-Admin + Disponenten |
| Nacherfassung | Papierprotokolle nacherfassen | Disponenten |
| Monitoring verstaerken | Erhoehte Aufmerksamkeit fuer 72 Stunden | IT-Admin |
| Post-Incident Review | Ursachenanalyse und Verbesserungen | ISB |
| Dokumentation | Vorfall und Massnahmen dokumentieren | ISB |

---

## 4. Notbetriebsverfahren

### 4.1 Papierbasierter Notbetrieb

Wenn OpMan_GPT nicht verfuegbar ist, wird auf papierbasierte Verfahren umgestellt:

| OpMan_GPT-Funktion | Notverfahren |
|-------------------|-------------|
| Einsatzuebersicht | Whiteboard mit Magnettafeln |
| Trupp-Status | Statuskarten (farbig) am Whiteboard |
| Einsatzzuordnung | Manuelle Zuordnung, Papiervordruck |
| Funkprotokoll | Handschriftliches Protokoll (Vordruck) |
| Falldokumentation | Einsatzprotokoll-Formular (Papier) |
| Alarmierung | Telefon, Funkruf |
| GPS-Tracking | Standortmeldung per Funk |

### 4.2 Vorgehaltene Materialien

- [ ] 50 Stueck Einsatzprotokoll-Vordrucke
- [ ] 50 Stueck Funkprotokoll-Vordrucke
- [ ] Whiteboard mit Magneten und Stiften
- [ ] Statusuebersicht-Poster (Funkstatus 0-9)
- [ ] Aktuelle Telefonliste aller Einsatzkraefte
- [ ] Karte des Einsatzgebiets (Papier, laminiert)
- [ ] Taschenlampe und Batterien (fuer Stromausfall)

---

## 5. Backup-Konzept

### 5.1 Backup-Strategie

| Element | Verfahren | Turnus | Aufbewahrung |
|---------|----------|--------|-------------|
| SQLite-Datenbank | Dateikopie (cp + gzip) | Taeglich, 02:00 Uhr | 30 Tage lokal + 90 Tage offsite |
| Encryption Key | Dateikopie (verschluesselt) | Bei Aenderung | Tresor (physisch) |
| VAPID Keys | Dateikopie | Bei Aenderung | Tresor |
| Konfiguration | Git-Repository | Bei Aenderung | Git-Server |
| Anwendungscode | Git-Repository | Bei Aenderung | Git-Server |
| Vollsicherung (System) | Image / tar.gz | Woechtentlich | 4 Wochen |

### 5.2 Backup-Restore-Prozess

```bash
# Backup erstellen (taeglich per Cron)
DATE=$(date +%Y%m%d_%H%M%S)
cp instance/einsatzleiter.db "backup/db_${DATE}.db"
gzip "backup/db_${DATE}.db"

# Optional: Verschluesselung
openssl enc -aes-256-cbc -salt -in "backup/db_${DATE}.db.gz" \
  -out "backup/db_${DATE}.db.gz.enc" -pass file:/path/to/backup-key

# Restore
gunzip backup/db_YYYYMMDD_HHMMSS.db.gz
cp backup/db_YYYYMMDD_HHMMSS.db instance/einsatzleiter.db
# Anwendung neu starten
```

### 5.3 Backup-Test

| Test | Turnus | Ergebnis dokumentieren |
|------|--------|----------------------|
| Restore-Test (Datenbank) | Monatlich | Ja |
| Vollstaendiger System-Restore | Quartalsweise | Ja |
| Offsite-Backup Zugriff | Quartalsweise | Ja |

---

## 6. Testplan

| Testtyp | Turnus | Teilnehmer | Ziel |
|---------|--------|-----------|------|
| Backup-Restore | Monatlich | IT-Admin | Restore < 30 Min, Daten integer |
| Failover auf Standby | Quartalsweise | IT-Admin, Schichtleiter | Umschaltung < 15 Min |
| Notbetrieb (Papier) | Halbjaehrlich | Leitstellenpersonal | Umstellung < 5 Min |
| Vollstaendiger BCM-Test | Jaehrlich | Alle Beteiligten | Kompletter Ablauf |
| Krisenstab-Uebung | Jaehrlich | GF, ISB, DSB, IT | Kommunikation, Entscheidungen |

---

## 7. Verantwortlichkeiten

| Rolle | BCM-Verantwortung |
|-------|-------------------|
| Geschaeftsfuehrung | BCM-Budget, Krisenentscheidungen, Kommunikation |
| IS-Beauftragter | BCM-Koordination, Testplanung, Dokumentation |
| IT-Administration | Technische Umsetzung, Backup, Restore, Monitoring |
| Schichtleiter (Leitstelle) | Umschaltung auf Notbetrieb, Nacherfassung |
| Disponenten | Notbetrieb durchfuehren, Papierprotokoll fuehren |
| DSB | Datenschutz im Notbetrieb, Meldepflichten |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
