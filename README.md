# OpMan GPT – Übungs- und Einsatzleitstand

Webbasiertes Einsatzleit- und Übungssystem für den Sanitätsdienst (BRK).
Läuft lokal im LAN – kein Cloud-Dienst, keine externen Abhängigkeiten im Betrieb.

---

## Schnellstart

```bash
pip install -r requirements.txt
python app.py
```

Aufruf im Browser: `http://<Server-IP>:5000`
Für iOS/Android (HTTPS erforderlich): Zertifikat unter `http://<IP>:5000/cert` installieren, dann `https://...` aufrufen.

---

## Funktionsübersicht

### Leitstellenansicht (`/`)

Die Hauptoberfläche für den Übungsleiter / Einsatzleiter.

#### Trupps (links)
- Trupps anlegen mit Name, Rufname, Farbe, Funkstatus (FMS 0–9), Verfügbarkeit, Funkgruppe
- Funkstatus direkt ändern (Dropdown)
- Position per Karteklick übernehmen oder manuell eingeben
- „auf Karte" springt zur Trupp-Position (behält aktuellen Zoomlevel)
- Trupp löschen

#### Einsätze (rechts)
- Einsätze anlegen mit Titel, Beschreibung, Priorität 1–5, Position
- Statusfarbe: Rot = kein Trupp, Gelb = zugewiesen, Grün = vor Ort/Transport
- Einsatzstatus ändern (offen → zugewiesen → in Arbeit → abgeschlossen)
- „auf Karte" springt zur Einsatzposition
- Einsatz löschen

#### Schnellkoordination (Mitte)
- Trupp (links) + Einsatz (rechts) auswählen → zuweisen
- Zuweisung aufheben
- Nur verfügbare Trupps (S1/S2, Verfügbarkeit = verfügbar) sind disponierbar

#### Karte
- OpenStreetMap mit Leaflet.js
- Trupp-Marker (farbige Kreise) und Einsatz-Marker (farbige Pins)
- Übungslayer mit P1–P6 Positionen + Verbindungslinien + Laufzeitschätzung
- Klick auf Karte → Koordinaten für Formularfelder übernehmen

#### Sprechwunsch-Panel
- Erscheint automatisch (fly-in, unten rechts) wenn ein Trupp S0 oder S5 meldet
- Zeigt: Rufname, Name, **Funkgruppe (📻 Regelfunk / 🏥 Bettenkanal)**, Uhrzeit, S0/S5-Badge
- Quittieren-Button setzt den Trupp zurück auf den vorherigen Funkstatus
- Akustische Warnung: S0 = 3 aufsteigende Töne, S5 = 2 kurze Töne

---

### Mobile EVT-App (`/evt`)

Optimiert für Smartphones im Hochformat.

- **Trupp-Auswahl**: Welcher EVT verwendet dieses Gerät
- **FMS-Buttons**: 3×3 Grid + S0-Vollzeile, farbkodiert
  - Grün: S1/S2 (frei), Gelb: S3 (auf Anfahrt), Blau: S4 (vor Ort)
  - Orange: S7/S8 (Transport/Ziel), Rot: S0/S5 (Sprechwunsch)
- **Alarm-Overlay**: Bei neuem Einsatz erscheint Overlay mit Falldetails, Ton und Vibration
- **Alarmton (WAV)**: Pre-rendered WAV-Blobs (kein Web Audio API) – funktioniert zuverlässig auf iOS/Android
- **Aktivierungs-Overlay**: Beim Seitenreload mit gespeichertem EVT erscheint „Tippe zum Starten" – sichert Audio-Freischaltung vor dem ersten Alarm
- **Alarm-Persistenz**: Quittierte Alarme werden in localStorage gespeichert, kein erneutes Overlay nach Seitenreload
- **Web Push Notifications**: Alarm-Benachrichtigungen auch bei geschlossenem Browser (PWA + Service Worker)
- **GPS-Tracking**: Position wird automatisch an den Server gesendet (alle ~10 Sek. oder ab 5m Bewegung)
- **Funkgruppen-Wechsel**: Umschalten zwischen Regelfunk und Bettenkanal
- **Fallkarte**: Zeigt den zugewiesenen Fall mit Schlagwort, Patient, w3w-Adresse, Zeitstempel
- **PWA-installierbar**: Kann auf dem Homescreen installiert werden (manifest.json)

---

### Funkprotokoll (`/protokoll`)

- Chronologisches Protokoll aller Funksprüche und Statusmeldungen
- Auto-Logging bei jedem Funkstatuswechsel
- Filter nach Fall (P1–P6)
- Manuelle Einträge möglich
- Einträge löschen

---

### Übungssystem

#### Vordefinierte Fälle P1–P6

| Fall | Schlagwort | Patient | Besonderheit |
|------|------------|---------|--------------|
| P1 | VU (schwer) – Radfahrer vs. PKW | Lennart Voigt, 27m | ABCD, RD + Polizei |
| P2 | Sturz Skateboard – Handgelenk | Elzbieta Szczepaniak, 19w | Namensfalle im Meldezettel |
| P3 | Atemnot – COPD-Exazerbation | Hakan Yilmaz, 62m | Adressfalle (falsche Einsatzadresse) |
| P4 | VU (leicht) – Auffahrunfall | Kevin Schäfer, 31m | Patient verweigert Transport |
| P5 | Schlaganfall – neurol. Ausfall | Jürgen Krämer, 72m | Stroke-Unit, Antikoagulation |
| P6 | Brustschmerz – V.a. ACS | Sabine Lutz, 56w | ASS-Allergie, Klinikwahl |

Alle Fälle haben eingebettete GPS-Koordinaten (Raum Feucht, Bayern) – keine Internet-Verbindung für die Kartendarstellung nötig.

#### Falldokumentation
- Zeitstempel: Alarmzeit, S3, S4, S7, S8
- Gemeldete Werte: PZC (6-stellig, kommagetrennte Soll-Werte)
- ABCD-Schema: Bewertung A/B/C/D mit 1–4 Skala (nur bei SK1, d.h. PZC 6. Stelle = 1)
- Zielklinik, Freitextnotizen
- Abschluss-Tracking pro EVT
- Abgeschlossene Fälle sind nicht mehr alarmierbar

#### Nachbesprechung & Auswertung
- PZC-Vergleich (Soll vs. Ist, kommagetrennt)
- ABCD-Schema-Bewertung (grün = genau richtig, gelb = knapp daneben, rot = falsch)
- Bewertung pro EVT-Team

#### Mehrfach-EVT-Betrieb
- Konfigurierbar: 1–6 EVT-Teams
- Derselbe Fall wird für jedes EVT separat abgearbeitet
- Globaler Abschluss wenn alle konfigurierten EVTs den Fall beendet haben

#### Import
- „Übungsfälle als Einsätze importieren" legt P1–P6 direkt als Einsätze mit Koordinaten an

---

## Technik

| Komponente | Technologie |
|------------|-------------|
| Backend | Python 3 / Flask 3 |
| Datenbank | SQLite via SQLAlchemy |
| Frontend | Vanilla JS (ES6+), CSS3 |
| Karte | Leaflet.js 1.9.4 + OpenStreetMap |
| Audio | Pre-rendered WAV-Blobs via `<audio>` Element |
| Push | Web Push API + Service Worker (pywebpush/VAPID) |
| GPS | Geolocation API (Browser) |
| HTTPS | Selbstsigniertes Zertifikat (optional, für Push/GPS Pflicht) |

Alle Daten bleiben lokal. Keine externen Dienste außer OpenStreetMap-Kartenkacheln.

---

## Datenbankmodelle

- **Team** – Name, Rufname, Farbe, Funkstatus, Verfügbarkeit, Funkgruppe, Position
- **Mission** – Titel, Beschreibung, Priorität, Status, Position
- **Assignment** – Trupp ↔ Einsatz Zuweisung
- **CaseDoc** – Falldokumentation (Zeitstempel, PZC, ABCD, Notizen, Abschluss)
- **RadioLogEntry** – Funkprotokolleinträge
- **ExerciseConfig** – EVT-Anzahl Konfiguration
- **PushSubscription** – Web-Push-Abonnements pro EVT-Gerät

---

## Offene Aufgaben

Siehe [TODO.md](TODO.md).
