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

### [ENHANCEMENT] Offline-Karten (Tile-Cache)
**Label:** `enhancement`

Kartenkacheln vorab herunterladen und lokal cachen, damit die Karte auch ohne Internet funktioniert.

**Technisch:**
- Service Worker fängt Tile-Requests ab und cached sie
- Oder: MBTiles-Datei + lokaler Tile-Server (z.B. `mbtileserver`)
- Fallback auf gecachte Tiles wenn offline

---

### [ENHANCEMENT] Einsatz-Replay / Zeitraffer
**Label:** `enhancement`

Nach der Übung: Wiedergabe des Einsatzverlaufs als Animation auf der Karte.

**Funktionen:**
- Zeitstrahl mit Play/Pause/Geschwindigkeit
- Trupp-Bewegungen (GPS-Trail) auf der Karte animieren
- Statuswechsel als Farbänderung der Marker
- Zeitpunkt-Einblendung: welches Team wo war, welcher Status

---

### [ENHANCEMENT] Checklisten pro Einsatzart
**Label:** `enhancement`

Vordefinierte Checklisten (z.B. „VU-Checkliste", „Internistischer Notfall") die dem EVT nach dem Alarm angezeigt werden.

**Anwendung:**
- EVT kann Punkte abhaken (z.B. „Absicherung", „Bodycheck", „Monitoring angelegt")
- Ergebnisse werden gespeichert und in der Nachbesprechung ausgewertet
- Checklisten im Admin-Bereich konfigurierbar

---

### [ENHANCEMENT] Nachrichten / Chat zwischen EL und EVT
**Label:** `enhancement`

Kurznachrichten vom Einsatzleiter an einzelne oder alle EVTs senden.

**Funktionen:**
- EL tippt Nachricht + wählt Empfänger (einzeln oder Broadcast)
- EVT sieht Nachricht als Toast/Popup
- Nützlich für Hinweise wie „Pause 10 Min" oder „Fall P3: Patient nicht auffindbar"

---

### [ENHANCEMENT] Bewertungsbogen / Noten pro EVT
**Label:** `enhancement`

Strukturierter Bewertungsbogen pro EVT nach Übungsende.

**Kriterien:**
- Zeitmanagement (Ausrückzeit, Vor-Ort-Zeit)
- Dokumentationsqualität (PZC korrekt, ABCD vollständig)
- Kommunikation (Funkdisziplin, korrekte Meldungen)
- Gesamtnote / Punktesystem

---

### [ENHANCEMENT] Dark/Light Mode Umschalter
**Label:** `enhancement`

Auf der Leitstellenansicht zwischen hellem und dunklem Design wechseln.
EVT-App ist bereits dunkel. Protokoll-Seite ebenfalls.

---

## Zu testen (Heutige Änderungen 28.02.2026)

### Aktivierungs-Overlay (Audio-Freischaltung)
- [ ] EVT-Seite laden mit gespeichertem EVT → „Tippe zum Starten" Overlay erscheint
- [ ] Auf „Starten" tippen → Overlay verschwindet, Polling beginnt
- [ ] Alarm auslösen → Alarmton spielt SOFORT (nicht erst nach Quittieren)
- [ ] Seitenreload → Overlay erscheint erneut (nicht direkt lospolling)

### Fertig-Checkbox verhindert Neualarmierung
- [ ] In `/protokoll`: Fall als „Fertig" markieren (Checkbox)
- [ ] Versuchen, denselben Fall erneut zu alarmieren → Fehlermeldung
- [ ] Alarm-Button ist ausgegraut / disabled bei abgeschlossenen Fällen
- [ ] EVT geht S1 → Fall wird NICHT recycelt (bleibt completed)

### Web Push Notifications
- [ ] EVT-Seite in Chrome/Edge öffnen → Notification-Permission wird angefragt
- [ ] Erlauben → Push-Subscription wird an Server gesendet
- [ ] **WICHTIG**: HTTPS erforderlich! Push funktioniert nur über HTTPS
- [ ] Browser komplett schließen → Alarm vom EL auslösen → Push-Notification erscheint
- [ ] Auf Notification tippen → EVT-App öffnet sich
- [ ] Tipp: App auf Homescreen installieren (PWA) für beste Ergebnisse

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
- [x] Web Push Notifications für EVT-App (Service Worker + VAPID + pywebpush)
- [x] Alarm-Sound: WAV-basierter Ansatz statt Web Audio API (iOS/Android-kompatibel)
- [x] Aktivierungs-Overlay bei Seitenreload (Audio-Freischaltung vor erstem Alarm)
- [x] Alarm-Persistenz in localStorage (kein erneutes Overlay nach Quittierung)
- [x] Nachbesprechung: RMI/SK entfernt, PZC mit Komma-Soll, ABCD-Bewertung
- [x] ABCD-Schema: Button-Selektion bleibt erhalten, korrekte Anzeige bei SK1 (6. Stelle)
- [x] PZC-Eingabe löst sofortige Auswertung aus (kein Warten auf Debounce)
- [x] Abgeschlossene Fälle sind nicht mehr alarmierbar (Server + Client)
