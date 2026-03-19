# Lessons Learned – Coding Assistant

## Projektübergreifende Erkenntnisse

### 2026-03-15 – Datenschutzerklärung vs. tatsächliches Verhalten

**Projekt:** OpMan-GPT Security-Audit
**Was passiert ist:** Die Datenschutzerklärung behauptet "GPS-Positionen werden nur im Arbeitsspeicher gehalten", aber tatsächlich werden sie in der SQLite-Datenbank persistiert (teams.lat, teams.lng). Außerdem steht "keine Übertragung an externe Server", aber die W3W-API sendet Standortdaten an what3words.com.
**Ursache:** Datenschutzerklärung wurde einmal geschrieben und danach nicht aktualisiert, als sich die technische Umsetzung geändert hat.
**Lösung:** Datenschutzerklärung mit dem tatsächlichen Verhalten abgleichen und korrigieren.
**Regel für die Zukunft:** Bei jeder technischen Änderung, die Datenverarbeitung betrifft, sofort die Datenschutzerklärung prüfen und aktualisieren. Ein Widerspruch zwischen Dokumentation und Code ist ein DSGVO-Verstoß.
**Kategorie:** Datenschutz

### 2026-03-15 – Jinja2 `| safe` Filter ist gefährlich

**Projekt:** OpMan-GPT Security-Audit
**Was passiert ist:** `{{ initial_data | safe }}` in einem `<script>`-Tag erlaubt JavaScript-Injection über Datenbank-Inhalte. Wenn ein Team-Name `</script><script>alert(1)</script>` enthält, wird der Code ausgeführt.
**Ursache:** `| safe` wurde verwendet, um JSON-Daten ohne HTML-Escaping in JavaScript einzubetten. Der richtige Filter wäre `| tojson`.
**Lösung:** `| safe` durch `| tojson` ersetzen – das escaped korrekt für JavaScript-Kontexte.
**Regel für die Zukunft:** Nie `| safe` verwenden, um Daten in `<script>`-Tags einzubetten. Immer `| tojson` für JSON-Daten in JavaScript. `| safe` nur verwenden, wenn der Inhalt nachweislich sicher ist (z.B. statische HTML-Fragmente).
**Kategorie:** Sicherheit

### 2026-03-15 – SECRET_KEY Fallback ist ein stilles Sicherheitsrisiko

**Projekt:** OpMan-GPT Security-Audit
**Was passiert ist:** `SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-in-production")` – wenn keine .env konfiguriert ist, verwendet Flask einen bekannten Schlüssel. Sessions könnten gefälscht werden.
**Ursache:** Entwickler-Komfort (App startet auch ohne Konfiguration) wurde über Sicherheit gestellt.
**Lösung:** Fallback entfernen und beim Start einen Fehler werfen, wenn SECRET_KEY nicht gesetzt ist.
**Regel für die Zukunft:** Sicherheitskritische Konfiguration (Secret Keys, API Keys, DB-Passwörter) NIEMALS mit bekannten Fallbacks versehen. Lieber den Start verweigern als unsicher laufen.
**Kategorie:** Sicherheit

### 2026-03-15 – innerHTML ist der häufigste XSS-Vektor in SPAs

**Projekt:** OpMan-GPT Security-Audit
**Was passiert ist:** Über 40 Stellen verwenden `innerHTML` mit Template-Literals. Eine `esc()`-Funktion existiert, wird aber inkonsequent eingesetzt – manche Werte werden escaped, andere nicht.
**Ursache:** Bei großen JavaScript-Templates mit vielen Variablen vergisst man leicht einzelne `esc()`-Aufrufe. Manuelles Escaping skaliert nicht.
**Lösung:** Entweder (1) konsequent alle interpolierten Werte mit `esc()` wrappen und per Code-Review prüfen, oder (2) auf ein Framework umsteigen, das Auto-Escaping bietet (React, Vue, lit-html).
**Regel für die Zukunft:** Bei Vanilla-JS-Projekten eine strikte Regel: Jede Variable in einem innerHTML-Template-Literal MUSS durch `esc()` laufen. Ausnahmen nur für hardcodierte HTML-Fragmente. Bei Reviews gezielt nach unescapten `${...}` in innerHTML suchen.
**Kategorie:** Sicherheit

### 2026-03-15 – Fehlende Auth in LAN-Apps ist kein Schutz

**Projekt:** OpMan-GPT Security-Audit
**Was passiert ist:** Alle API-Endpoints sind ohne Authentifizierung zugänglich. Das Argument "ist ja nur im LAN" greift nicht – in einem Übungsszenario mit vielen mobilen Geräten kann jeder Teilnehmer (oder jemand im selben WLAN) Daten löschen, Reset auslösen oder Updates erzwingen.
**Ursache:** Übungssystem wurde als "internes Tool" betrachtet, Sicherheit nicht priorisiert.
**Lösung:** Mindestens HTTP Basic Auth für administrative Endpoints (Reset, Update, Team-Verwaltung).
**Regel für die Zukunft:** Auch interne/LAN-Tools brauchen Zugriffskontrolle. Die Frage ist nicht "wer könnte angreifen", sondern "was passiert, wenn jemand versehentlich oder absichtlich den falschen Button drückt". Ein einfacher Passwortschutz für kritische Funktionen kostet 30 Minuten, spart aber potenziell eine ruinierte Übung.
**Kategorie:** Architektur

### 2026-03-19 – Parallele Agenten brauchen sauberes Merging

**Projekt:** OpMan-GPT – 6 Feature-Enhancements parallel
**Was passiert ist:** 6 Sub-Agenten haben gleichzeitig an app.py, models.py und Templates gearbeitet. Die meisten Änderungen wurden korrekt zusammengeführt, aber die Auswertungs-Routen (/auswertung, /api/auswertung) und die Sicherheitsfixes (SECRET_KEY, W3W_API_KEY) fehlten nach dem Merge.
**Ursache:** Worktree-basierte Agenten haben jeweils ihre eigene Kopie bearbeitet. Beim Zurückmergen wurden einige Änderungen überschrieben.
**Lösung:** Manueller Verifikations-Scan nach dem Merge: Jede erwartete Route/Funktion per grep prüfen, Syntax-Check ausführen.
**Regel für die Zukunft:** Nach parallelen Agent-Änderungen IMMER eine Checkliste der erwarteten Änderungen erstellen und per grep/syntax-check verifizieren. Nie blind darauf vertrauen, dass Merges vollständig sind.
**Kategorie:** Architektur

### 2026-03-19 – W3W Reverse-Geocoding braucht HTML-Element

**Projekt:** OpMan-GPT – W3W-Kartenintegration
**Was passiert ist:** JavaScript-Code für Reverse-W3W referenzierte `document.getElementById("lastClickW3w")`, aber das HTML-Element existierte nicht in index.html.
**Ursache:** JS und HTML wurden in verschiedenen Phasen bearbeitet – das HTML-Element wurde vergessen.
**Lösung:** `<span id="lastClickW3w">—</span>` in der .maphud-Sektion eingefügt.
**Regel für die Zukunft:** Bei Frontend-Features immer die vollständige Kette prüfen: HTML-Element → CSS-Styling → JavaScript-Logik → API-Endpoint. Wenn eins fehlt, funktioniert nichts.
**Kategorie:** Debugging
