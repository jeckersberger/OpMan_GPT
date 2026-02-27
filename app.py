from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from sqlalchemy import text
from models import db, Team, Mission, Assignment, CaseDoc, RadioLogEntry, ExerciseConfig

# ---------------------------
# Funkstatus (Code -> Text)
# ---------------------------
RADIO_STATUS_LABELS: dict[int, str] = {
    1:  "Frei auf Funk",
    2:  "Frei auf Wache",
    3:  "Einsatz übernommen",
    4:  "Am Einsatzort",
    5:  "Sprechwunsch",
    6:  "nicht Einsatzbereit",
    7:  "Patient aufgenommen",
    8:  "Am Transportziel",
    9:  "Sonderfunktion",
    0:  "prio. Sprechwunsch",
}

# ---------------------------
# Verfügbarkeit (Disposition)
# ---------------------------
ALLOWED_AVAILABILITY = {"verfügbar", "bedingt", "nicht_verfügbar"}

# Optional (empfohlen): welche Funkstatus gelten als "disponierbar"?
# Wenn du ALLE "availability=verfügbar" zulassen willst, setze DISPATCHABLE... = None
DISPATCHABLE_RADIO_STATUSES: set[int] | None = {1, 2}  # frei auf Funk / frei auf Wache

# ---------------------------
# what3words API
# ---------------------------
W3W_API_KEY = "2ZJ55EYB"
W3W_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "w3w_cache.json")
STARTPUNKT_W3W = "dulden.ausgehend.erscheinende"


def resolve_w3w(words: str):
    """Resolve a what3words address to (lat, lng). Returns (None, None) on error.

    Uses a direct connection (proxy bypassed) so that system proxy env-vars set
    by development environments (e.g. Claude Code sandbox) don't interfere.
    Falls back to the system default if the direct attempt fails with a DNS error.
    """
    clean = words.lstrip("/")
    url = (
        "https://api.what3words.com/v3/convert-to-coordinates"
        f"?words={urllib.parse.quote(clean)}&key={W3W_API_KEY}"
    )
    # Try 1: direct connection (bypass HTTP_PROXY / HTTPS_PROXY env vars)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        if "coordinates" in data:
            return data["coordinates"]["lat"], data["coordinates"]["lng"]
    except OSError as e:
        # DNS failure → server has no direct internet, try via system proxy
        if "Name or service not known" in str(e) or "Temporary failure" in str(e) or getattr(e, 'errno', None) == -3:
            try:
                with urllib.request.urlopen(url, timeout=8) as resp:  # noqa: S310
                    data = json.loads(resp.read().decode())
                if "coordinates" in data:
                    return data["coordinates"]["lat"], data["coordinates"]["lng"]
            except Exception:
                pass
    except Exception:
        pass
    return None, None


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///einsatzleiter.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Übungs-Falldaten (statisch, aus Übungsleiterunterlagen)
    EXERCISE_CASES = {
        "P1": {
            "schlagwort": "VU (schwer) – Radfahrer vs. PKW",
            "patient": "Lennart Voigt", "alter": 27, "geschlecht": "m",
            "w3w": "///erstes.arbeitswelt.spülmittel", "w3w_alarm": None,
            "lat": 49.377493, "lng": 11.206863,
            "rmi_soll": "211", "sk_soll": "1", "pzc_soll": "211271",
            "besonderheit": "Pflichtfall ABCD-Schema (SK1). RD + POL auf Anfahrt.",
        },
        "P2": {
            "schlagwort": "Sturz Skateboard – Handgelenksverletzung",
            "patient": "Elzbieta Szczepaniak", "alter": 19, "geschlecht": "w",
            "patient_alarm": "Lisa Schneider",   # falscher Name in der Alarmierung
            "w3w": "///vorweisen.kanone.möchte", "w3w_alarm": None,
            "lat": 49.377035, "lng": 11.202390,
            "rmi_soll": "272", "sk_soll": "3", "pzc_soll": "272193",
            "besonderheit": "Name in Alarmierung falsch (Lisa Schneider). Buchstabieren erforderlich.",
        },
        "P3": {
            "schlagwort": "Atemnot – COPD-Exazerbation",
            "patient": "Hakan Yilmaz", "alter": 62, "geschlecht": "m",
            "w3w": "///wunder.untersuchen.lacke",
            "w3w_alarm": "///geiger.kerzen.besonders",
            "lat": 49.379595, "lng": 11.208106,
            "rmi_soll": "312", "sk_soll": "2", "pzc_soll": "312622",
            "besonderheit": "Adressfalle: Alarmadresse falsch. Korrektur erst nach Rückmeldung 'keine Lage'.",
        },
        "P4": {
            "schlagwort": "VU (leicht) – Auffahrunfall",
            "patient": "Kevin Schäfer", "alter": 31, "geschlecht": "m",
            "w3w": "///zumal.genügt.hellbraun", "w3w_alarm": None,
            "lat": 49.381131, "lng": 11.202597,
            "rmi_soll": "—", "sk_soll": "—", "pzc_soll": "—",
            "besonderheit": "Fokus: Lagemeldung + Nachforderung (Gefahrenlage erkennen). Patient lehnt Transport ab.",
        },
        "P5": {
            "schlagwort": "Schlaganfall – neurologischer Ausfall",
            "patient": "Jürgen Krämer", "alter": 72, "geschlecht": "m",
            "w3w": "///familienname.haltung.aufdeckung", "w3w_alarm": None,
            "lat": 49.373262, "lng": 11.201692,
            "rmi_soll": "421", "sk_soll": "2", "pzc_soll": "421722",
            "besonderheit": "Stroke-Klinik. Fokus auf PZC / Klinikwahl. Antikoagulation beachten.",
        },
        "P6": {
            "schlagwort": "Brustschmerz – V.a. ACS",
            "patient": "Sabine Lutz", "alter": 56, "geschlecht": "w",
            "w3w": "///obenrum.kranz.wählen", "w3w_alarm": None,
            "lat": 49.375283, "lng": 11.204709,
            "rmi_soll": "331", "sk_soll": "2", "pzc_soll": "331562",
            "besonderheit": "ASS-Allergie! Fokus auf PZC / Klinikwahl.",
        },
    }
    STARTPUNKT_LAT = 49.378328
    STARTPUNKT_LNG = 11.204336

    with app.app_context():
        db.create_all()
        # Auto-migration: add new columns to existing tables
        _migrations = [
            "ALTER TABLE teams ADD COLUMN radio_group VARCHAR(30) NOT NULL DEFAULT 'regelfunk'",
            "ALTER TABLE case_docs ADD COLUMN completed_evts TEXT NOT NULL DEFAULT '[]'",
            "ALTER TABLE teams ADD COLUMN gps_updated_at DATETIME",
            "ALTER TABLE teams ADD COLUMN test_alarm_at DATETIME",
            "ALTER TABLE teams ADD COLUMN test_alarm_text VARCHAR(200)",
        ]
        with db.engine.connect() as _conn:
            for _sql in _migrations:
                try:
                    _conn.execute(text(_sql))
                    _conn.commit()
                except Exception:
                    pass  # Column already exists
        # CaseDoc-Einträge initialisieren (nur beim ersten Start)
        for case_id in EXERCISE_CASES:
            if CaseDoc.query.get(case_id) is None:
                db.session.add(CaseDoc(id=case_id))
        # ExerciseConfig Singleton
        if ExerciseConfig.query.get(1) is None:
            db.session.add(ExerciseConfig(id=1, evt_count=6))
        db.session.commit()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/protokoll")
    def protokoll():
        return render_template("protokoll.html", cases=EXERCISE_CASES)

    @app.get("/api/server-info")
    def server_info():
        """Gibt die LAN-IP-Adresse des Servers zurück (für Handy-QR-Code)."""
        import socket as _socket
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            s.close()
        except Exception:
            lan_ip = "127.0.0.1"
        port = 5000
        # HTTPS wenn Zertifikat vorhanden (run.py wurde verwendet)
        _cert = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "instance", "cert.pem")
        proto = "https" if os.path.exists(_cert) else "http"
        return jsonify({
            "ip": lan_ip,
            "port": port,
            "base_url": f"{proto}://{lan_ip}:{port}",
            "evt_url":  f"{proto}://{lan_ip}:{port}/evt",
        })

    @app.get("/api/test-internet")
    def test_internet():
        """Quick connectivity check: tries to reach api.what3words.com directly."""
        import time
        results = {}
        test_url = (
            f"https://api.what3words.com/v3/convert-to-coordinates"
            f"?words=filled.count.soap&key={W3W_API_KEY}"
        )
        # Direct (no proxy)
        t0 = time.time()
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(test_url, timeout=6) as r:
                data = json.loads(r.read().decode())
            results["direct"] = {"ok": True, "ms": int((time.time()-t0)*1000),
                                  "coords": data.get("coordinates")}
        except Exception as e:
            results["direct"] = {"ok": False, "error": str(e), "ms": int((time.time()-t0)*1000)}
        # Via system proxy
        t0 = time.time()
        try:
            with urllib.request.urlopen(test_url, timeout=6) as r:  # noqa: S310
                data = json.loads(r.read().decode())
            results["proxy"] = {"ok": True, "ms": int((time.time()-t0)*1000),
                                 "coords": data.get("coordinates")}
        except Exception as e:
            results["proxy"] = {"ok": False, "error": str(e), "ms": int((time.time()-t0)*1000)}
        ok = results["direct"]["ok"] or results["proxy"]["ok"]
        return jsonify({"internet": ok, "results": results})

    @app.get("/evt")
    def evt_mobile():
        return render_template("evt.html", cases=EXERCISE_CASES)

    # ---------------------------
    # EVT Mobile Status API
    # ---------------------------
    @app.get("/api/evt-status/<string:evt_name>")
    def get_evt_status(evt_name: str):
        """Liefert Team-Status + aktiver Fall für ein EVT-Team (Mobile-App)."""
        team = Team.query.filter(
            (Team.name == evt_name) | (Team.callsign == evt_name)
        ).first()

        docs = CaseDoc.query.filter_by(assigned_evt=evt_name).all()
        active_doc = None
        if docs:
            # Nur aktive (nicht abgeschlossene) Fälle anzeigen
            active = [d for d in docs if d.alarm_time and not d.completed]
            if active:
                active_doc = max(active, key=lambda d: d.alarm_time)

        case_meta = EXERCISE_CASES.get(active_doc.id) if active_doc else None
        # pending_alarm: Alarm ausgelöst, aber S3 noch nicht bestätigt
        _pa = bool(active_doc and active_doc.alarm_time and not active_doc.status3_time)
        return jsonify({
            "team": serialize_team(team, pending_alarm=_pa) if team else None,
            "case": serialize_casedoc(active_doc) if active_doc else None,
            "case_meta": case_meta,
        })

    # ---------------------------
    # CaseDoc API
    # ---------------------------
    @app.get("/api/casedocs")
    def list_casedocs():
        docs = CaseDoc.query.order_by(CaseDoc.id).all()
        return jsonify([serialize_casedoc(d) for d in docs])

    @app.patch("/api/casedocs/<string:case_id>")
    def update_casedoc(case_id: str):
        doc = CaseDoc.query.get_or_404(case_id)
        data = request.get_json(force=True)

        for field in ("assigned_evt", "rmi_reported", "sk_reported",
                      "pzc_reported", "zielklinik", "notes"):
            if field in data:
                setattr(doc, field, (data[field] or "").strip() or None)

        if "completed" in data:
            doc.completed = bool(data["completed"])

        # Zeitstempel-Felder (ISO-String oder null)
        for ts_field in ("alarm_time", "status3_time", "status4_time",
                         "status7_time", "status8_time"):
            if ts_field in data:
                val = data[ts_field]
                if val:
                    try:
                        setattr(doc, ts_field,
                                datetime.fromisoformat(val.replace("Z", "+00:00"))
                                        .replace(tzinfo=None))
                    except (ValueError, AttributeError):
                        pass
                else:
                    setattr(doc, ts_field, None)

        doc.updated_at = datetime.utcnow()
        _sync_team_from_doc(doc)
        db.session.commit()
        return jsonify(serialize_casedoc(doc))

    @app.post("/api/casedocs/<string:case_id>/stamp")
    def stamp_casedoc(case_id: str):
        """Setzt einen Zeitstempel auf 'jetzt'."""
        doc = CaseDoc.query.get_or_404(case_id)
        data = request.get_json(force=True)
        field = data.get("field")
        allowed = {"alarm_time", "status3_time", "status4_time",
                   "status7_time", "status8_time"}
        if field not in allowed:
            return jsonify({"error": "unknown field"}), 400
        setattr(doc, field, datetime.utcnow())
        doc.updated_at = datetime.utcnow()
        _sync_team_from_doc(doc)
        db.session.commit()
        return jsonify(serialize_casedoc(doc))

    # ---------------------------
    # RadioLog API
    # ---------------------------
    @app.get("/api/radiolog")
    def list_radiolog():
        entries = RadioLogEntry.query.order_by(RadioLogEntry.timestamp.desc()).all()
        return jsonify([serialize_logentry(e) for e in entries])

    @app.post("/api/radiolog")
    def create_logentry():
        data = request.get_json(force=True)
        sender = (data.get("sender") or "").strip()
        if not sender:
            return jsonify({"error": "sender is required"}), 400
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"error": "message is required"}), 400

        ts_raw = data.get("timestamp")
        if ts_raw:
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, AttributeError):
                ts = datetime.utcnow()
        else:
            ts = datetime.utcnow()

        entry = RadioLogEntry(
            timestamp=ts,
            sender=sender,
            receiver=(data.get("receiver") or "").strip() or None,
            fms_status=int(data["fms_status"]) if data.get("fms_status") is not None else None,
            case_ref=(data.get("case_ref") or "").strip() or None,
            message=message,
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify(serialize_logentry(entry)), 201

    @app.delete("/api/radiolog/<int:entry_id>")
    def delete_logentry(entry_id: int):
        entry = RadioLogEntry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"ok": True})

    # ---------------------------
    # Reset
    # ---------------------------
    @app.post("/api/reset")
    def reset_exercise():
        """Vollständiger Übungs-Reset.

        Body (alle optional, default False):
          include_log    – Funkprotokoll leeren
          reset_teams    – Trupps auf S1/verfügbar zurücksetzen (Positionen behalten)
          delete_teams   – Trupps und Einsätze komplett löschen
        """
        data = request.get_json(force=True) or {}
        include_log  = bool(data.get("include_log",  False))
        reset_teams  = bool(data.get("reset_teams",  True))
        delete_teams = bool(data.get("delete_teams", False))
        now = datetime.utcnow()

        # 1. CaseDocs zurücksetzen
        for doc in CaseDoc.query.all():
            doc.assigned_evt   = None
            doc.alarm_time     = None
            doc.status3_time   = None
            doc.status4_time   = None
            doc.status7_time   = None
            doc.status8_time   = None
            doc.rmi_reported   = None
            doc.sk_reported    = None
            doc.pzc_reported   = None
            doc.zielklinik     = None
            doc.notes          = None
            doc.completed      = False
            doc.completed_evts = "[]"
            doc.updated_at     = now

        # 2. Alle Zuweisungen löschen
        Assignment.query.delete()

        # 3. Missions auf "offen" zurücksetzen
        for m in Mission.query.all():
            m.status     = "offen"
            m.updated_at = now

        # 4. Trupps
        if delete_teams:
            Mission.query.delete()
            Team.query.delete()
        elif reset_teams:
            for t in Team.query.all():
                t.radio_status   = 1
                t.availability   = "verfügbar"
                t.test_alarm_at  = None
                t.test_alarm_text = None
                t.updated_at     = now

        # 5. Funkprotokoll
        if include_log:
            RadioLogEntry.query.delete()

        db.session.commit()
        return jsonify({"ok": True})

    # ---------------------------
    # Exercise Geodata (what3words)
    # ---------------------------
    @app.get("/api/exercise/geodata")
    def exercise_geodata():
        """Return exercise case coordinates (built directly from EXERCISE_CASES)."""
        result: dict = {"cases": {}, "startpunkt": None}
        for case_id, cd in EXERCISE_CASES.items():
            result["cases"][case_id] = {
                "lat": cd.get("lat"),
                "lng": cd.get("lng"),
                "schlagwort": cd["schlagwort"],
                "patient": cd["patient"],
                "w3w": cd["w3w"],
            }
        result["startpunkt"] = {"lat": STARTPUNKT_LAT, "lng": STARTPUNKT_LNG, "w3w": STARTPUNKT_W3W}
        return jsonify(result)

    @app.get("/cert")
    def download_cert():
        """Serve self-signed certificate for iOS/Android installation."""
        cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "instance", "cert.pem")
        if not os.path.exists(cert_path):
            return "Kein Zertifikat vorhanden. Zuerst gen_cert.py ausführen.", 404
        from flask import send_file
        return send_file(cert_path, mimetype="application/x-pem-file",
                         as_attachment=True, download_name="OpManGPT.pem")

    # ---------------------------
    # Exercise Config
    # ---------------------------
    @app.get("/api/exercise/config")
    def get_exercise_config():
        cfg = ExerciseConfig.query.get(1)
        return jsonify({"evt_count": cfg.evt_count if cfg else 6})

    @app.post("/api/exercise/config")
    def update_exercise_config():
        cfg = ExerciseConfig.query.get_or_404(1)
        data = request.get_json(force=True)
        if "evt_count" in data:
            n = int(data["evt_count"])
            if not (1 <= n <= 6):
                return jsonify({"error": "evt_count must be 1-6"}), 400
            cfg.evt_count = n
        db.session.commit()
        return jsonify({"evt_count": cfg.evt_count})

    @app.post("/api/exercise/import-missions")
    def import_exercise_missions():
        """Erstellt Missions aus den Übungsfällen (Koordinaten aus Cache, falls vorhanden)."""
        geodata: dict = {"cases": {}, "startpunkt": None}
        if os.path.exists(W3W_CACHE_FILE):
            try:
                with open(W3W_CACHE_FILE) as f:
                    geodata = json.load(f)
            except Exception:
                pass

        created = []
        for case_id, cd in EXERCISE_CASES.items():
            geo = (geodata.get("cases") or {}).get(case_id, {})
            lat = geo.get("lat") or cd.get("lat")
            lng = geo.get("lng") or cd.get("lng")
            title = f"{case_id}: {cd['schlagwort']}"
            # Nicht doppelt anlegen
            existing = Mission.query.filter_by(title=title).first()
            if existing:
                # Koordinaten nachpflegen, falls sie fehlen oder sich geändert haben
                if existing.lat != lat or existing.lng != lng:
                    existing.lat = lat
                    existing.lng = lng
                    existing.updated_at = datetime.utcnow()
                created.append({"id": existing.id, "title": title, "skipped": True})
                continue
            m = Mission(
                title=title,
                description=cd.get("besonderheit") or None,
                priority=1 if cd.get("sk_soll") == "1" else 3,
                status="offen",
                lat=lat,
                lng=lng,
                updated_at=datetime.utcnow(),
            )
            db.session.add(m)
            db.session.flush()
            created.append({"id": m.id, "title": title, "skipped": False})
        db.session.commit()
        return jsonify({"created": created})

    # ---------------------------
    # Teams
    # ---------------------------
    @app.get("/api/teams")
    def list_teams():
        teams = Team.query.order_by(Team.updated_at.desc()).all()
        # Alarmierte aber noch nicht quittierte Teams (alarm_time gesetzt, status3_time noch nicht)
        _pending_evts = {
            d.assigned_evt for d in CaseDoc.query.filter(
                CaseDoc.alarm_time.isnot(None),
                CaseDoc.status3_time.is_(None),
                CaseDoc.completed == False  # noqa: E712
            ).all() if d.assigned_evt
        }
        result = []
        for t in teams:
            _ident = {t.name, t.callsign} - {None}
            result.append(serialize_team(
                t, include_missions=True,
                pending_alarm=bool(_ident & _pending_evts)
            ))
        return jsonify(result)

    @app.get("/api/teams/available")
    def list_available_teams():
        q = Team.query.filter(Team.availability == "verfügbar")
        if DISPATCHABLE_RADIO_STATUSES is not None:
            q = q.filter(Team.radio_status.in_(list(DISPATCHABLE_RADIO_STATUSES)))
        teams = q.order_by(Team.updated_at.desc()).all()
        return jsonify([serialize_team(t, include_missions=True) for t in teams])

    @app.post("/api/teams")
    def create_team():
        data = request.get_json(force=True)

        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name is required"}), 400

        availability = (data.get("availability") or "verfügbar").strip()
        if availability not in ALLOWED_AVAILABILITY:
            return jsonify({"error": "availability must be verfügbar|bedingt|nicht_verfügbar"}), 400

        radio_status = int(data.get("radio_status") if data.get("radio_status") is not None else 1)
        if radio_status not in RADIO_STATUS_LABELS:
            return jsonify({"error": "radio_status not allowed"}), 400

        color = (data.get("color") or "#4ea1ff").strip() or "#4ea1ff"

        team = Team(
            name=name,
            callsign=(data.get("callsign") or "").strip() or None,
            availability=availability,
            radio_status=radio_status,
            color=color,
            lat=data.get("lat"),
            lng=data.get("lng"),
            updated_at=datetime.utcnow(),
        )
        db.session.add(team)
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True)), 201

    @app.patch("/api/teams/<int:team_id>")
    def update_team(team_id: int):
        team = Team.query.get_or_404(team_id)
        data = request.get_json(force=True)

        if "name" in data:
            team.name = (data["name"] or "").strip() or team.name

        if "callsign" in data:
            team.callsign = (data["callsign"] or "").strip() or None

        if "availability" in data:
            av = (data["availability"] or team.availability).strip()
            if av not in ALLOWED_AVAILABILITY:
                return jsonify({"error": "availability must be verfügbar|bedingt|nicht_verfügbar"}), 400
            team.availability = av

        if "radio_group" in data:
            rg = (data["radio_group"] or "regelfunk").strip().lower()
            if rg not in {"regelfunk", "bettenkanal"}:
                return jsonify({"error": "radio_group must be regelfunk|bettenkanal"}), 400
            team.radio_group = rg

        if "radio_status" in data:
            rs = int(data["radio_status"])
            if rs not in RADIO_STATUS_LABELS:
                return jsonify({"error": "radio_status not allowed"}), 400
            team.radio_status = rs

            # Status 1 (Frei auf Funk) → alle Einsatzzuweisungen automatisch aufheben
            if rs == 1:
                for assignment in list(team.assignments):
                    mission = assignment.mission
                    db.session.delete(assignment)
                    db.session.flush()
                    # Mission auf "offen" zurücksetzen falls keine weiteren Teams mehr
                    remaining = Assignment.query.filter_by(mission_id=mission.id).first()
                    if not remaining and mission.status == "zugewiesen":
                        mission.status = "offen"
                        mission.updated_at = datetime.utcnow()
                team.availability = "verfügbar"

            # Aktiven CaseDoc suchen → Zeitstempel spiegeln + ggf. abschließen
            # Neuester nicht-abgeschlossener Fall mit alarm_time hat Vorrang
            _stamp_map = {3: "status3_time", 4: "status4_time",
                          7: "status7_time", 8: "status8_time"}
            _ident = {team.name, team.callsign} - {None}
            _case_ref = None
            for _i in _ident:
                _doc = (CaseDoc.query
                        .filter_by(assigned_evt=_i)
                        .filter(CaseDoc.alarm_time.isnot(None),
                                CaseDoc.completed == False)  # noqa: E712
                        .order_by(CaseDoc.alarm_time.desc())
                        .first())
                if _doc:
                    _case_ref = _doc.id
                    _field = _stamp_map.get(rs)
                    if _field and getattr(_doc, _field) is None:
                        setattr(_doc, _field, datetime.utcnow())
                        _doc.updated_at = datetime.utcnow()
                    # S1 nach S4 oder S8 → diesen EVT als erledigt markieren
                    if rs == 1 and (_doc.status4_time is not None
                                    or _doc.status8_time is not None):
                        _done_case_id = _doc.id
                        # EVT in completed_evts eintragen
                        _evt_done = _doc.assigned_evt or ""
                        _evts = json.loads(_doc.completed_evts or "[]")
                        if _evt_done and _evt_done not in _evts:
                            _evts.append(_evt_done)
                        _doc.completed_evts = json.dumps(_evts)
                        # Prüfen ob alle EVTs fertig sind
                        _cfg = ExerciseConfig.query.get(1)
                        _total = _cfg.evt_count if _cfg else 6
                        _globally_done = len(_evts) >= _total
                        if _globally_done:
                            # Alle EVTs durch → global abschließen
                            _doc.completed = True
                        else:
                            # Noch weitere EVTs → Felder zurücksetzen für nächsten Einsatz
                            _doc.assigned_evt = None
                            _doc.alarm_time   = None
                            _doc.status3_time = None
                            _doc.status4_time = None
                            _doc.status7_time = None
                            _doc.status8_time = None
                            _doc.completed    = False
                        _doc.updated_at = datetime.utcnow()
                        # Mission abschließen + Assignment dieses Teams aufheben
                        for _dm in Mission.query.filter(
                            Mission.title.like(f"{_done_case_id}:%")
                        ).all():
                            _dm.status = "abgeschlossen"
                            _dm.updated_at = datetime.utcnow()
                            _del_a = Assignment.query.filter_by(
                                team_id=team.id, mission_id=_dm.id
                            ).first()
                            if _del_a:
                                db.session.delete(_del_a)
                    break
            _auto_log(team, rs, case_ref=_case_ref)

        if "color" in data:
            team.color = (data["color"] or team.color).strip() or team.color

        if "lat" in data:
            team.lat = data["lat"]
        if "lng" in data:
            team.lng = data["lng"]
        if ("lat" in data or "lng" in data) and data.get("gps"):
            team.gps_updated_at = datetime.utcnow()

        team.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True))

    @app.post("/api/teams/<int:team_id>/quittieren")
    def quittieren_team(team_id: int):
        """Quittiert einen Sprechwunsch (S0/S5) und setzt das Team auf den Vorgänger-Status zurück."""
        team = Team.query.get_or_404(team_id)
        if team.radio_status not in {0, 5}:
            return jsonify({"error": "Kein aktiver Sprechwunsch"}), 400

        sw_status = team.radio_status  # 0 oder 5
        _ident = {team.name, team.callsign} - {None}

        # Vorgänger-Status: letzter Log-Eintrag des Teams vor dem S0/S5
        restore_rs = 1  # Default
        last_log = (RadioLogEntry.query
                    .filter(RadioLogEntry.sender.in_(list(_ident)),
                            RadioLogEntry.fms_status.notin_([0, 5]),
                            RadioLogEntry.fms_status.isnot(None))
                    .order_by(RadioLogEntry.timestamp.desc())
                    .first())
        if last_log:
            restore_rs = last_log.fms_status

        # case_ref für den Log-Eintrag
        _case_ref = None
        for _i in _ident:
            _doc = (CaseDoc.query.filter_by(assigned_evt=_i)
                    .filter(CaseDoc.alarm_time.isnot(None),
                            CaseDoc.completed == False)  # noqa: E712
                    .order_by(CaseDoc.alarm_time.desc()).first())
            if _doc:
                _case_ref = _doc.id
                break

        team.radio_status = restore_rs
        team.updated_at = datetime.utcnow()

        sw_label = RADIO_STATUS_LABELS.get(sw_status, f"S{sw_status}")
        rs_label  = RADIO_STATUS_LABELS.get(restore_rs, f"S{restore_rs}")
        db.session.add(RadioLogEntry(
            timestamp=datetime.utcnow(),
            sender="FüSt",
            receiver=team.callsign or team.name,
            fms_status=restore_rs,
            case_ref=_case_ref,
            message=f"{sw_label} quittiert – zurück auf FMS {restore_rs} ({rs_label})",
            created_at=datetime.utcnow(),
        ))
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True))

    @app.delete("/api/teams/<int:team_id>")
    def delete_team(team_id: int):
        team = Team.query.get_or_404(team_id)
        db.session.delete(team)
        db.session.commit()
        return jsonify({"ok": True})

    # ---------------------------
    # Testalarm
    # ---------------------------
    @app.post("/api/testalarm")
    def send_testalarm():
        """Sendet einen Testalarm an ausgewählte Teams oder alle.

        Body: { "team_ids": [1, 2], "text": "Testalarm!" }
              { "all": true, "text": "Testalarm an alle!" }
        """
        data = request.get_json(force=True)
        text = (data.get("text") or "Testalarm").strip()[:200]
        now = datetime.utcnow()

        if data.get("all"):
            targets = Team.query.all()
        else:
            ids = data.get("team_ids") or []
            targets = Team.query.filter(Team.id.in_(ids)).all()

        if not targets:
            return jsonify({"error": "Keine Teams ausgewählt"}), 400

        for team in targets:
            team.test_alarm_at   = now
            team.test_alarm_text = text
            team.updated_at      = now

        db.session.commit()
        return jsonify({"ok": True, "sent_to": [t.id for t in targets]})

    @app.delete("/api/testalarm/<int:team_id>")
    def clear_testalarm(team_id: int):
        """EVT quittiert den Testalarm."""
        team = Team.query.get_or_404(team_id)
        team.test_alarm_at   = None
        team.test_alarm_text = None
        team.updated_at      = datetime.utcnow()
        db.session.commit()
        return jsonify({"ok": True})

    # ---------------------------
    # Missions
    # ---------------------------
    @app.get("/api/missions")
    def list_missions():
        missions = Mission.query.order_by(Mission.updated_at.desc()).all()
        return jsonify([serialize_mission(m, include_teams=True) for m in missions])

    @app.post("/api/missions")
    def create_mission():
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title is required"}), 400

        mission = Mission(
            title=title,
            description=(data.get("description") or "").strip() or None,
            priority=int(data.get("priority") or 3),
            status=(data.get("status") or "offen"),
            lat=data.get("lat"),
            lng=data.get("lng"),
            updated_at=datetime.utcnow(),
        )
        db.session.add(mission)
        db.session.commit()
        return jsonify(serialize_mission(mission, include_teams=True)), 201

    @app.patch("/api/missions/<int:mission_id>")
    def update_mission(mission_id: int):
        mission = Mission.query.get_or_404(mission_id)
        data = request.get_json(force=True)

        if "title" in data:
            mission.title = (data["title"] or "").strip() or mission.title
        if "description" in data:
            mission.description = (data["description"] or "").strip() or None
        if "priority" in data:
            mission.priority = int(data["priority"] or mission.priority)
        if "status" in data:
            mission.status = data["status"] or mission.status
        if "lat" in data:
            mission.lat = data["lat"]
        if "lng" in data:
            mission.lng = data["lng"]

        mission.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(serialize_mission(mission, include_teams=True))

    @app.delete("/api/missions/<int:mission_id>")
    def delete_mission(mission_id: int):
        mission = Mission.query.get_or_404(mission_id)
        db.session.delete(mission)
        db.session.commit()
        return jsonify({"ok": True})

    # ---------------------------
    # Assignments (Team <-> Mission)
    # ---------------------------
    @app.get("/api/assignments")
    def list_assignments():
        assigns = Assignment.query.order_by(Assignment.created_at.desc()).all()
        return jsonify([serialize_assignment(a) for a in assigns])

    @app.post("/api/assignments")
    def create_assignment():
        data = request.get_json(force=True)
        team_id = data.get("team_id")
        mission_id = data.get("mission_id")

        if not team_id or not mission_id:
            return jsonify({"error": "team_id and mission_id required"}), 400

        team = Team.query.get_or_404(int(team_id))
        mission = Mission.query.get_or_404(int(mission_id))

        # Nur verfügbare Teams zuweisen
        if team.availability != "verfügbar":
            return jsonify({"error": f"Team ist nicht verfügbar (availability: {team.availability})"}), 409

        # Optional: nur disponierbare Funkstatus zuweisen
        if DISPATCHABLE_RADIO_STATUSES is not None and team.radio_status not in DISPATCHABLE_RADIO_STATUSES:
            return jsonify({"error": f"Team ist nicht disponierbar (Funkstatus: {team.radio_status})"}), 409

        existing = Assignment.query.filter_by(team_id=team.id, mission_id=mission.id).first()
        if existing:
            return jsonify(serialize_assignment(existing)), 200

        a = Assignment(team_id=team.id, mission_id=mission.id)
        db.session.add(a)

        # Mission: offen -> zugewiesen
        if mission.status == "offen":
            mission.status = "zugewiesen"
            mission.updated_at = datetime.utcnow()

        # Team: nach Zuweisung optional Availability umstellen
        # (damit es nicht weiter als verfügbar angeboten wird)
        team.availability = "bedingt"
        team.updated_at = datetime.utcnow()

        # CaseDoc alarmieren: Mission-Titel hat Format "P1: Schlagwort"
        _parts = mission.title.split(":", 1)
        _mission_case_id = _parts[0].strip() if len(_parts) >= 2 else None
        if _mission_case_id:
            _cdoc = CaseDoc.query.get(_mission_case_id)
            if _cdoc and not _cdoc.alarm_time and not _cdoc.completed:
                _cdoc.assigned_evt = team.name
                _cdoc.alarm_time   = datetime.utcnow()
                _cdoc.updated_at   = datetime.utcnow()

        db.session.commit()
        return jsonify(serialize_assignment(a)), 201

    @app.delete("/api/assignments/<int:assignment_id>")
    def delete_assignment(assignment_id: int):
        a = Assignment.query.get_or_404(assignment_id)

        team = a.team  # Team merken bevor wir löschen
        db.session.delete(a)
        db.session.commit()

        # Prüfen ob Team noch irgendeinem Einsatz zugewiesen ist
        still_assigned = Assignment.query.filter_by(team_id=team.id).first() is not None

        if not still_assigned:
            # Team wieder verfügbar machen
            team.availability = "verfügbar"
            team.updated_at = datetime.utcnow()
            db.session.commit()

        return jsonify({"ok": True})

    return app


# ---------------------------
# Synchronisation-Helfer
# ---------------------------
def _auto_log(team: "Team", rs: int, case_ref: str | None = None) -> None:
    """Erstellt automatisch einen RadioLogEntry für eine FMS-Statusänderung."""
    label = RADIO_STATUS_LABELS.get(rs, f"S{rs}")
    name = team.callsign or team.name
    entry = RadioLogEntry(
        timestamp=datetime.utcnow(),
        sender=name,
        receiver="FüSt",
        fms_status=rs,
        case_ref=case_ref,
        message=f"FMS {rs} – {label}",
        created_at=datetime.utcnow(),
    )
    db.session.add(entry)


def _sync_team_from_doc(doc: "CaseDoc") -> None:
    """Leitet den aktuellen FMS-Status aus einem CaseDoc ab und setzt ihn am Team.
    Wird gerufen nachdem ein Zeitstempel in der Falldokumentation gesetzt wurde."""
    if not doc.assigned_evt:
        return
    team = Team.query.filter(
        (Team.name == doc.assigned_evt) | (Team.callsign == doc.assigned_evt)
    ).first()
    if not team:
        return

    # Höchsten gesetzten Zeitstempel → FMS-Status ableiten
    if doc.completed:
        rs = 1
    elif doc.status8_time:
        rs = 8
    elif doc.status7_time:
        rs = 7
    elif doc.status4_time:
        rs = 4
    elif doc.status3_time:
        rs = 3
    else:
        return  # Nichts gesetzt → kein Update

    if team.radio_status == rs:
        return  # Schon korrekt, kein Eintrag nötig

    team.radio_status = rs
    team.updated_at = datetime.utcnow()
    _auto_log(team, rs, case_ref=doc.id)


# ---------------------------
# Serialization
# ---------------------------
def serialize_casedoc(d: CaseDoc):
    def fmt(dt):
        return (dt.isoformat() + "Z") if dt else None
    return {
        "id":            d.id,
        "assigned_evt":  d.assigned_evt,
        "alarm_time":    fmt(d.alarm_time),
        "status3_time":  fmt(d.status3_time),
        "status4_time":  fmt(d.status4_time),
        "status7_time":  fmt(d.status7_time),
        "status8_time":  fmt(d.status8_time),
        "rmi_reported":  d.rmi_reported,
        "sk_reported":   d.sk_reported,
        "pzc_reported":  d.pzc_reported,
        "zielklinik":    d.zielklinik,
        "notes":         d.notes,
        "completed":     d.completed,
        "completed_evts": json.loads(getattr(d, "completed_evts", None) or "[]"),
        "updated_at":    fmt(d.updated_at),
    }


def serialize_logentry(e: RadioLogEntry):
    return {
        "id":         e.id,
        "timestamp":  (e.timestamp.isoformat() + "Z"),
        "sender":     e.sender,
        "receiver":   e.receiver,
        "fms_status": e.fms_status,
        "case_ref":   e.case_ref,
        "message":    e.message,
        "created_at": (e.created_at.isoformat() + "Z"),
    }


def serialize_team(t: Team, include_missions: bool = False, pending_alarm: bool = False):
    payload = {
        "id": t.id,
        "name": t.name,
        "callsign": t.callsign,
        "availability": t.availability,
        "radio_status": t.radio_status,
        "radio_status_label": RADIO_STATUS_LABELS.get(t.radio_status, "unbekannt"),
        "radio_group": getattr(t, "radio_group", "regelfunk") or "regelfunk",
        "color": t.color,
        "lat": t.lat,
        "lng": t.lng,
        "gps_updated_at":  t.gps_updated_at.isoformat() + "Z" if t.gps_updated_at else None,
        "test_alarm_at":   t.test_alarm_at.isoformat() + "Z" if t.test_alarm_at else None,
        "test_alarm_text": t.test_alarm_text,
        "updated_at": t.updated_at.isoformat() + "Z",
        "pending_alarm": pending_alarm,
    }

    if include_missions:
        payload["missions"] = [
            {
                "id": a.mission.id,
                "title": a.mission.title,
                "status": a.mission.status,
                "priority": a.mission.priority,
            }
            for a in sorted(t.assignments, key=lambda x: x.created_at, reverse=True)
        ]
    return payload


def serialize_mission(m: Mission, include_teams: bool = False):
    payload = {
        "id": m.id,
        "title": m.title,
        "description": m.description,
        "priority": m.priority,
        "status": m.status,
        "lat": m.lat,
        "lng": m.lng,
        "updated_at": m.updated_at.isoformat() + "Z",
    }

    if include_teams:
        payload["teams"] = [
            {
                "id": a.team.id,
                "name": a.team.name,
                "callsign": a.team.callsign,
                "availability": a.team.availability,
                "radio_status": a.team.radio_status,
                "radio_status_label": RADIO_STATUS_LABELS.get(a.team.radio_status, "unbekannt"),
                "color": a.team.color,
            }
            for a in sorted(m.assignments, key=lambda x: x.created_at, reverse=True)
        ]
    return payload


def serialize_assignment(a: Assignment):
    return {
        "id": a.id,
        "team_id": a.team_id,
        "mission_id": a.mission_id,
        "created_at": a.created_at.isoformat() + "Z",
        "team": {
            "id": a.team.id,
            "name": a.team.name,
            "callsign": a.team.callsign,
            "availability": a.team.availability,
            "radio_status": a.team.radio_status,
            "radio_status_label": RADIO_STATUS_LABELS.get(a.team.radio_status, "unbekannt"),
            "color": a.team.color,
        },
        "mission": {
            "id": a.mission.id,
            "title": a.mission.title,
            "status": a.mission.status,
            "priority": a.mission.priority,
        },
    }


if __name__ == "__main__":
    # Hinweis: Wenn du von der alten DB-Struktur kommst,
    # lösche einmal die Datei "einsatzleiter.db", damit die neuen Spalten
    # (availability etc.) sauber erstellt werden.
    #
    # Nutze 'python run.py' für HTTPS mit Auto-Zertifikat (empfohlen).
    # 'python app.py' startet ebenfalls mit HTTPS falls möglich.
    import os, subprocess, socket

    INSTANCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    CERT = os.path.join(INSTANCE_DIR, "cert.pem")
    KEY  = os.path.join(INSTANCE_DIR, "key.pem")

    def _get_lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _ensure_cert():
        if os.path.exists(CERT) and os.path.exists(KEY):
            return True
        lan_ip = _get_lan_ip()
        os.makedirs(INSTANCE_DIR, exist_ok=True)
        cnf_path = os.path.join(INSTANCE_DIR, "san.cnf")
        with open(cnf_path, "w") as f:
            f.write(f"""[req]
default_bits       = 2048
prompt             = no
distinguished_name = dn
x509_extensions    = v3_req

[dn]
CN = OpMan-GPT Local

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
IP.1 = {lan_ip}
IP.2 = 127.0.0.1
DNS.1 = localhost
""")
        print(f"Generiere SSL-Zertifikat für {lan_ip} ...")
        result = subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", KEY, "-out", CERT, "-days", "825", "-config", cnf_path,
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Warnung: openssl fehlgeschlagen – Fallback auf HTTP")
            return False
        print(f"  Zertifikat erstellt: {CERT}")
        return True

    app = create_app()
    lan_ip = _get_lan_ip()
    ssl_ctx = (CERT, KEY) if _ensure_cert() else None
    proto = "https" if ssl_ctx else "http"
    print()
    print("=" * 60)
    print(f"  OpMan-GPT startet mit {proto.upper()}")
    print(f"  {proto}://{lan_ip}:5000        ← LAN (Handy)")
    print(f"  {proto}://localhost:5000        ← lokal")
    if not ssl_ctx:
        print("  ⚠  GPS funktioniert NICHT über HTTP auf iOS/Android!")
    print("=" * 60)
    print()
    app.run(debug=True, host="0.0.0.0", port=5000, ssl_context=ssl_ctx)
