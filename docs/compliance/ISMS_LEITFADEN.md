# ISMS-Leitfaden

**Dokument:** Leitfaden zur Einfuehrung eines Informationssicherheits-Managementsystems
**System:** OpMan_GPT -- Einsatzleitsoftware
**Version:** 1.0
**Datum:** 04.03.2026
**Klassifikation:** Intern

---

## 1. Einleitung

Dieses Dokument beschreibt den Aufbau eines Informationssicherheits-Managementsystems (ISMS) fuer den Betrieb der Einsatzleitsoftware OpMan_GPT. Als KRITIS-relevante Organisation im Bereich Rettungsdienst ist ein ISMS gemaess ss 30 BSIG (NIS2UmsuCG) verpflichtend.

---

## 2. ISO 27001 vs. BSI IT-Grundschutz -- Vergleich

| Kriterium | ISO/IEC 27001:2022 | BSI IT-Grundschutz |
|-----------|-------------------|-------------------|
| **Herkunft** | Internationale Norm (ISO) | Deutsches BSI-Framework |
| **Ansatz** | Risikobasiert (Top-down) | Massnahmenbasiert (Bottom-up) mit Risikoanalyse |
| **Detailtiefe** | Abstrakte Anforderungen (93 Controls, Annex A) | Sehr detaillierte Bausteine und Massnahmen |
| **Sprache** | Englisch (DE-Uebersetzung) | Deutsch |
| **Anwendbarkeit** | Universal, branchenuebergreifend | Primaer DE/DACH, oeffentl. Verwaltung |
| **Zertifizierung** | ISO 27001-Zertifikat (akkreditiert) | ISO 27001 auf Basis IT-Grundschutz |
| **Aufwand** | Mittel bis hoch | Hoch (detaillierte Modellierung) |
| **KRITIS-Konformitaet** | Anerkannt gemaess ss 8a BSIG | Explizit empfohlen vom BSI |
| **BSI-Anerkennung** | Ja (B3S-Grundlage) | Ja (bevorzugt) |
| **Kosten Zertifizierung** | Ca. 15.000 - 40.000 EUR | Ca. 20.000 - 50.000 EUR |
| **Gueltigkeitsdauer** | 3 Jahre (jaehrliche Ueberwachungsaudits) | 3 Jahre (jaehrliche Ueberwachungsaudits) |

### Empfehlung fuer OpMan_GPT

Fuer den Rettungsdienst-Kontext empfehlen wir **BSI IT-Grundschutz** als primaeres Framework, da:
1. Es vom BSI explizit fuer KRITIS-Betreiber empfohlen wird
2. Detaillierte, deutschsprachige Umsetzungshinweise verfuegbar sind
3. Eine Zertifizierung "ISO 27001 auf Basis IT-Grundschutz" beides abdeckt
4. Die Abstimmung mit BSI als Aufsichtsbehoerde einfacher ist

---

## 3. BSI IT-Grundschutz -- Umsetzung

### 3.1 Relevante BSI-Standards

| Standard | Inhalt |
|----------|--------|
| BSI-Standard 200-1 | Managementsysteme fuer Informationssicherheit |
| BSI-Standard 200-2 | IT-Grundschutz-Methodik |
| BSI-Standard 200-3 | Risikoanalyse auf Basis IT-Grundschutz |
| BSI-Standard 200-4 | Business Continuity Management |

### 3.2 Relevante IT-Grundschutz-Bausteine

| Baustein | Bezeichnung | Relevanz fuer OpMan_GPT |
|----------|------------|------------------------|
| ISMS.1 | Sicherheitsmanagement | Pflicht |
| ORP.1 | Organisation | Pflicht |
| ORP.2 | Personal | Pflicht |
| ORP.3 | Sensibilisierung und Schulung | Pflicht |
| ORP.4 | Identitaets- und Berechtigungsmanagement | Pflicht |
| CON.1 | Kryptokonzept | Pflicht |
| CON.2 | Datenschutz | Pflicht |
| CON.3 | Datensicherungskonzept | Pflicht |
| CON.6 | Loeschen und Vernichten | Pflicht |
| CON.7 | Informationssicherheit auf Reisen | Optional |
| OPS.1.1.2 | Ordnungsgemaesse IT-Administration | Pflicht |
| OPS.1.1.3 | Patch- und Aenderungsmanagement | Pflicht |
| OPS.1.1.4 | Schutz vor Schadprogrammen | Pflicht |
| OPS.1.1.5 | Protokollierung | Pflicht |
| OPS.1.1.6 | Software-Tests und Freigaben | Pflicht |
| OPS.1.2.4 | Telearbeit | Falls zutreffend |
| OPS.1.2.5 | Fernwartung | Falls zutreffend |
| DER.1 | Detektion von sicherheitsrel. Ereignissen | Pflicht |
| DER.2.1 | Behandlung von Sicherheitsvorfaellen | Pflicht |
| DER.4 | Notfallmanagement | Pflicht |
| APP.3.1 | Webanwendungen und Webservices | Pflicht |
| APP.4.3 | Relationale Datenbanksysteme | Pflicht |
| SYS.1.1 | Allgemeiner Server | Pflicht |
| SYS.1.3 | Server unter Linux/Unix | Pflicht |
| NET.1.1 | Netzarchitektur und -design | Pflicht |
| NET.3.1 | Router und Switches | Pflicht |
| NET.3.2 | Firewall | Pflicht |
| INF.1 | Allgemeines Gebaeude | Pflicht |
| INF.2 | Rechenzentrum / Serverraum | Pflicht |

---

## 4. Implementierungsfahrplan

### Phase 1: Vorbereitung (Wochen 1-4)

```
Woche 1-2: Projekt-Setup
  - Projektauftrag durch Geschaeftsfuehrung
  - IS-Beauftragten benennen
  - Projektteam zusammenstellen
  - Geltungsbereich definieren

Woche 3-4: Dokumentation Grundlagen
  - IS-Leitlinie erstellen
  - IS-Organisation definieren
  - Rollen und Verantwortlichkeiten festlegen
  - Kommunikationsplan erstellen
```

### Phase 2: Bestandsaufnahme (Wochen 5-12)

```
Woche 5-6: Strukturanalyse
  - Geschaeftsprozesse identifizieren
  - IT-Systeme inventarisieren
  - Netzplan erstellen/aktualisieren
  - Anwendungen dokumentieren

Woche 7-8: Schutzbedarfsfeststellung
  - Schutzbedarf pro Geschaeftsprozess
  - Schutzbedarf pro IT-System
  - Vererbung des Schutzbedarfs
  - Dokumentation der Ergebnisse

Woche 9-12: IT-Grundschutz-Modellierung
  - Bausteine den Zielobjekten zuordnen
  - IT-Grundschutz-Check durchfuehren
  - Ergaenzende Risikoanalyse (BSI 200-3)
  - Massnahmenplan erstellen
```

### Phase 3: Umsetzung (Wochen 13-36)

```
Woche 13-20: Technische Massnahmen
  - Firewall-Konfiguration
  - Netzwerk-Segmentierung
  - Server-Haertung
  - Backup-Konzept umsetzen
  - Monitoring einrichten
  - IDS/IPS implementieren

Woche 21-28: Organisatorische Massnahmen
  - Richtlinien erstellen
  - Prozesse dokumentieren
  - Schulungen durchfuehren
  - Notfallhandbuch erstellen
  - Lieferantenmanagement aufbauen

Woche 29-36: Validierung
  - Internes Audit
  - Penetrationstest
  - Massnahmen nachjustieren
  - Management-Review
```

### Phase 4: Zertifizierung (Wochen 37-48)

```
Woche 37-40: Zertifizierungsvorbereitung
  - Dokumentation finalisieren
  - Interne Audit-Ergebnisse aufbereiten
  - Zertifizierungsstelle auswaehlen
  - Voraudit (optional)

Woche 41-44: Zertifizierungsaudit Stufe 1
  - Dokumentenpruefung
  - Audit-Plan fuer Stufe 2 erstellen

Woche 45-48: Zertifizierungsaudit Stufe 2
  - Vor-Ort-Audit
  - Interviews und Stichproben
  - Massnahmen-Nachweise
  - Zertifikatserteilung
```

---

## 5. Zertifizierungsprozess

### 5.1 Voraussetzungen

- [ ] ISMS mindestens 3 Monate operativ in Betrieb
- [ ] Mindestens ein internes Audit durchgefuehrt
- [ ] Mindestens ein Management-Review durchgefuehrt
- [ ] Dokumentation vollstaendig und aktuell
- [ ] Korrekturmassnahmen aus internem Audit umgesetzt

### 5.2 Zertifizierungsstellen (BSI-anerkannt)

| Stelle | Spezialisierung |
|--------|----------------|
| BSI (direkt) | IT-Grundschutz-Zertifizierung |
| TUeV Rheinland | ISO 27001, IT-Grundschutz |
| TUeV Sued | ISO 27001, KRITIS |
| DQS | ISO 27001 |
| datenschutz cert | Datenschutz + IS |

### 5.3 Kosten-Uebersicht (Schaetzung)

| Position | Kosten (ca.) |
|----------|-------------|
| IS-Beauftragter (intern/extern) | 60.000 - 100.000 EUR/Jahr |
| Beratung/Implementierung | 30.000 - 80.000 EUR |
| Schulungen | 5.000 - 15.000 EUR |
| Penetrationstest | 5.000 - 20.000 EUR |
| Zertifizierungsaudit | 15.000 - 40.000 EUR |
| Jaehrliche Ueberwachungsaudits | 8.000 - 15.000 EUR |
| Technische Massnahmen (IDS, SIEM etc.) | 10.000 - 50.000 EUR |
| **Gesamt (Jahr 1)** | **125.000 - 305.000 EUR** |
| **Jaehrlich fortlaufend** | **80.000 - 150.000 EUR** |

---

## 6. Rollen und Verantwortlichkeiten

| Rolle | Verantwortlichkeit |
|-------|-------------------|
| Geschaeftsfuehrung | IS-Leitlinie, Budget, Management-Review, Haftung |
| IS-Beauftragter (ISB) | Aufbau/Betrieb ISMS, Risikoanalyse, Audits |
| IT-Leitung | Technische Umsetzung, Patch-Management, Betrieb |
| Datenschutzbeauftragter | DSGVO-Compliance, Zusammenarbeit mit ISB |
| Fachabteilungen | Schutzbedarfsfeststellung, Mitwirkung bei Audits |
| Alle Mitarbeiter | Einhaltung der IS-Richtlinien, Meldung von Vorfaellen |

---

## 7. Dokumentationspflichten

### Pflicht-Dokumente fuer Zertifizierung

- [ ] IS-Leitlinie (von GF unterschrieben)
- [ ] Geltungsbereich (Scope)
- [ ] Risikoanalyse und -behandlung
- [ ] Erklaerung zur Anwendbarkeit (SoA)
- [ ] Risikobehandlungsplan
- [ ] Sicherheitskonzept
- [ ] Asset-Inventar
- [ ] Zugangs- und Zugriffsrichtlinie
- [ ] Kryptokonzept
- [ ] Backup-Konzept
- [ ] Patch-Management-Richtlinie
- [ ] Incident-Response-Plan
- [ ] BCM-Plan / Notfallhandbuch
- [ ] Schulungsplan und -nachweise
- [ ] Interne Audit-Berichte
- [ ] Management-Review-Protokoll
- [ ] Korrekturmassnahmen-Tracking

---

## 8. KPIs fuer Informationssicherheit

| KPI | Zielwert | Messturnus |
|-----|----------|-----------|
| Sicherheitsvorfaelle (schwer) | 0 | Monatlich |
| Patch-Abdeckungsquote (kritisch) | > 95% innerhalb 7 Tagen | Monatlich |
| Schulungsquote Mitarbeiter | 100% | Jaehrlich |
| Ergebnis Penetrationstest | Keine kritischen Befunde | Jaehrlich |
| Backup-Erfolgsquote | 100% | Woechtentlich |
| Backup-Restore-Test erfolgreich | 100% | Quartalsweise |
| Mean Time to Detect (MTTD) | < 1 Stunde | Quartalsweise |
| Mean Time to Respond (MTTR) | < 4 Stunden | Quartalsweise |
| Access Review durchgefuehrt | 100% | Quartalsweise |

---

## Dokumenthistorie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|-----------|
| 1.0 | 04.03.2026 | [Name] | Erstfassung |
