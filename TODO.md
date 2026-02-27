# Issues / Offene Aufgaben

Dieses Dokument dient als Issue-Tracker.
Zum Anlegen als echte Git-Issues: Titel + Beschreibung ins Gitea-Web-Interface kopieren.

---

## Offen

---

### [BUG] GPS-Tracking der Trupps in Hauptkarte integrieren
**Label:** `bug` `enhancement`

Die EVT-App sendet bereits GPS-Koordinaten an den Server (`PATCH /api/teams/<id>`),
aber auf der Leitstellenansicht werden Trupp-Marker nicht automatisch aktualisiert
sobald sich die Position ändert.

**Erwartetes Verhalten:**
- Trupp-Marker bewegt sich live auf der Karte wenn EVT-App GPS sendet
- Visueller Unterschied: manuell gesetzte Position vs. live GPS (z.B. Puls-Animation)
- Letztes Positions-Update als Tooltip sichtbar

**Mögliche Erweiterung:**
- Genauigkeitsradius als Leaflet-Circle
- Bewegungsrichtung als Pfeil am Marker

---

### [ENHANCEMENT] Übungs-Reset mit einem Klick
**Label:** `enhancement`

Nach einem Übungsdurchlauf alle Daten für einen Neudurchlauf zurücksetzen,
ohne die Seite neu aufsetzen oder die Datenbank manuell löschen zu müssen.

**Umfang:**
- Alle Falldokumentationen (CaseDoc) zurücksetzen (Zeitstempel, Werte, Abschluss-Status)
- Alle Zuweisungen (Assignments) löschen
- Funkprotokoll leeren (optional: Bestätigung vorher)
- Trupps und Einsätze wahlweise behalten oder auch löschen
- Button auf der Leitstellenansicht, nur nach Bestätigung ausführen

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

### [ENHANCEMENT] Manuelle Protokolleinträge über die UI
**Label:** `enhancement`

Aktuell können freie Funksprüche nur über die REST-API eingetragen werden.
Der Übungsleiter soll direkt auf der Leitstellenseite einen Freitext-Eintrag
ins Protokoll schreiben können (z.B. für Anmerkungen oder externe Meldungen).

**UI:** kleines Eingabefeld im Funkprotokoll-Panel oder auf `/protokoll`

---

### [ENHANCEMENT] Übungs-Timer / Stoppuhr
**Label:** `enhancement`

Sichtbarer Timer auf der Leitstellenansicht der die laufende Übungszeit anzeigt.

**Funktionen:**
- Start / Pause / Reset
- Automatischer Start beim ersten Alarm (optional)
- Anzeige prominent im Header oder als festes Element auf der Karte
- Zeit wird im Funkprotokoll als Referenz mitgeloggt

---

### [ENHANCEMENT] Trupp-Bulk-Reset (alle auf S1 / verfügbar)
**Label:** `enhancement`

Ein einzelner Button der alle Trupps gleichzeitig auf Funkstatus 1 und
Verfügbarkeit „verfügbar" zurücksetzt — nützlich nach einem Übungsdurchlauf
oder wenn versehentlich falsche Statusmeldungen gesetzt wurden.

**UI:** Button in der Trupp-Leiste, nur nach Bestätigung ausführen

---

### [ENHANCEMENT] Kartenlayer wechseln
**Label:** `enhancement`

Aktuell nur OpenStreetMap. Für Gelände-/Einsatzübungen wären weitere Layer nützlich.

**Optionen:**
- OpenStreetMap (Standard)
- Satellite (z.B. Esri World Imagery, kostenlos)
- OpenTopoMap
- Layer-Auswahl als Leaflet Control (Standard-Leaflet-Feature, einfach einzubauen)

---

### [ENHANCEMENT] Status-Verlauf / Zeitleiste pro Trupp
**Label:** `enhancement`

Kompakte Zeitleiste der Statuswechsel pro Trupp für die Nachbesprechung —
z.B. „Trupp Alpha: S1 08:12 → S3 08:14 → S4 08:19 → S7 08:31 → S1 08:47"

**Darstellung:**
- Als ausklappbarer Bereich in der Trupp-Karte (Leitstellenansicht)
- Oder als eigene Spalte auf `/protokoll` gruppiert nach Trupp
- Daten aus dem Funkprotokoll ableiten (RadioLogEntry)

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

### [ENHANCEMENT] Mehrere Übungskurse parallel
**Label:** `enhancement`

Aktuell können nur alle EVTs denselben Übungssatz P1–P6 bearbeiten.
Für größere Ausbildungsveranstaltungen wäre paralleler Betrieb mehrerer
Kurse nützlich.

**Konzept:**
- Kurse als separate Namespaces (Kurs A, Kurs B, …)
- Jeder Kurs hat eigene Trupps, Falldokus und Protokoll
- Leitstellenansicht kann zwischen Kursen wechseln
- Größere Datenbankänderung notwendig

---

## Erledigt

- [x] Übungsfälle P1–P6 mit eingebetteten GPS-Koordinaten (kein w3w-API nötig)
- [x] Sprechwunsch-Panel: Name/Rufname lesbar, 2-Spalten Regelfunk/Bettenkanal
- [x] „auf Karte"-Buttons behalten aktuellen Zoomlevel
- [x] Mobile EVT-App: Alarm-Overlay, FMS-Buttons, GPS-Tracking
- [x] Funkprotokoll mit Auto-Logging bei Statuswechseln
- [x] Mehrfachteam-Übung: Fallabschluss wenn alle EVTs fertig
