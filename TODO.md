# Issues / Offene Aufgaben

Dieses Dokument dient als Issue-Tracker.
Zum Anlegen als echte Git-Issues: Titel + Beschreibung ins Gitea-Web-Interface kopieren.

---

## Offen

---

### [ENHANCEMENT] Einsatz-Auswertung nach Übungsende
**Label:** `enhancement`

Automatische Zeitstempel-Auswertung pro Fall nach Abschluss der Übung.

**Inhalt der Auswertung:**
- Alarmzeit → S3 (Reaktionszeit / Ausrückzeit)
- S3 → S4 (Anfahrtsdauer)
- S4 → S7 (Vor-Ort-Zeit)
- S7 → S8 (Transportdauer)
- Gesamtdauer pro Fall
- Vergleich zwischen EVT-Teams wenn mehrere teilgenommen haben

**Ausgabe:** eigene Seite `/auswertung` oder Modal auf der Protokoll-Seite

---

### [ENHANCEMENT] Funkprotokoll exportieren (PDF / CSV)
**Label:** `enhancement`

Das Funkprotokoll als Datei exportieren für die Nachbesprechung.

**Anforderungen:**
- CSV-Export: Zeitstempel, Sender, Empfänger, FMS, Fallbezug, Freitext
- PDF-Export: formatiertes Protokoll mit Übungs-Header (Datum, Ort, EVT-Anzahl)
- Filter vor Export möglich (nach Fall oder Zeitraum)
- Button auf `/protokoll`-Seite

---

### [ENHANCEMENT] Status-Verlauf / Zeitleiste pro Trupp
**Label:** `enhancement`

Kompakte Zeitleiste der Statuswechsel pro Trupp für die Nachbesprechung —
z.B. „EVT 1: S1 08:12 → S3 08:14 → S4 08:19 → S7 08:31 → S1 08:47"

**Darstellung:**
- Als ausklappbarer Bereich in der Trupp-Karte (Leitstellenansicht)
- Oder als eigene Spalte auf `/protokoll` gruppiert nach Trupp
- Daten aus dem Funkprotokoll ableiten (RadioLogEntry)

**Hinweis:** Fall-basierte Zeitleiste (P1–P6) existiert bereits auf `/protokoll`.
Hier geht es um die trupp-basierte Ansicht.

---

### [ENHANCEMENT] Web Push Notifications für EVT-App
**Label:** `enhancement`

Aktuell erhält die EVT-App neue Einsätze nur über den 10-Sekunden-Poll und
das Alarm-Overlay. Web Push würde Benachrichtigungen auch bei minimiertem Browser
ermöglichen.

**Technisch:**
- Service Worker + Push API (Browser-seitig)
- Push-Subscription in der Datenbank speichern
- Server sendet Push bei neuem Alarm (`/api/missions` POST + Assignment)
- Nur für HTTPS-Betrieb (bereits unterstützt)

---

## Erledigt

- [x] Übungsfälle P1–P6 mit eingebetteten GPS-Koordinaten (kein w3w-API nötig)
- [x] Sprechwunsch-Panel: Name/Rufname lesbar, 2-Spalten Regelfunk/Bettenkanal
- [x] „auf Karte"-Buttons behalten aktuellen Zoomlevel
- [x] Mobile EVT-App: Alarm-Overlay, FMS-Buttons, GPS-Tracking
- [x] Funkprotokoll mit Auto-Logging bei Statuswechseln
- [x] Mehrfachteam-Übung: Fallabschluss wenn alle EVTs fertig
- [x] Deployment: `deploy.sh` + `INSTALL.md` für Server (nginx + Let's Encrypt) und Raspi
- [x] GPS-Tracking der Trupps in Hauptkarte (Live-Pulse + manuell/GPS-Unterscheidung)
- [x] Übungs-Reset mit einem Klick (Modal mit Optionen)
- [x] Manuelle Protokolleinträge über die UI (Formular auf `/protokoll`)
- [x] Übungs-Timer / Stoppuhr (Start/Pause/Reset im Header)
- [x] Kartenlayer wechseln (OSM, Satellit, Topo)
- [x] HTTPS-Support mit Auto-Zertifikat (Windows/Linux/macOS)
- [x] EVT-Erstellung vereinfacht (Auto-Name „EVT 1, 2, …" + optionaler Rufname)
- [x] SQLAlchemy LegacyAPIWarning behoben (Query.get → Session.get)
- [x] Verbindungsstatus-Banner im Dashboard
- [x] GPS-Accuracy Farbfeedback im EVT (grün/gelb/orange)
- [x] /health Monitoring-Endpoint
