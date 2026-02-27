# TODO / Offene Aufgaben

## In Arbeit / Geplant

### Standortortung der Einsatztrupps
- [ ] **GPS-Tracking der Trupps in die Hauptkarte integrieren**
  - EVT-App sendet bereits Koordinaten an den Server (PATCH `/api/teams/<id>`)
  - Auf der Hauptkarte (Leitstellenansicht) sollen Trupp-Marker automatisch auf
    die gemeldete GPS-Position aktualisiert werden
  - Marker soll Richtung/Bewegung anzeigen (optional: Heading-Pfeil)
  - Genauigkeitsradius als Leaflet-Circle einblenden (optional)
  - Letztes Update-Timestamp im Popup anzeigen
  - Unterscheidung: manuell gesetzte Position vs. live GPS-Position (z.B. durch
    anderes Icon oder Pulsanimation)

## Ideen / Backlog

- [ ] Protokoll-Seite: Filter nach Zeitraum, Export als PDF/CSV
- [ ] Einsatzabschluss-Zusammenfassung: Auswertung der Zeitstempel pro Fall
- [ ] Mehrere gleichzeitige Übungen (mehrere Kurse parallel)
- [ ] Benutzer-/Rollenmanagement (Leitstellenführer, Übungsleiter, EVT)
- [ ] Dark/Light-Mode Toggle

## Erledigt

- [x] Übungsfälle P1–P6 mit eingebetteten GPS-Koordinaten (kein w3w-API nötig)
- [x] Sprechwunsch-Panel: Name/Rufname lesbar, Funkgruppe sichtbar
- [x] „auf Karte"-Buttons behalten aktuellen Zoomlevel
- [x] Mobile EVT-App: Alarm-Overlay, FMS-Buttons, GPS-Tracking
- [x] Funkprotokoll mit Auto-Logging bei Statuswechseln
- [x] Mehrfachteam-Übung: Fallabschluss wenn alle EVTs fertig
