from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

# ── Auto-install optionaler Abhängigkeiten ──
def _ensure_package(import_name: str, pip_spec: str) -> None:
    try:
        __import__(import_name)
    except ImportError:
        print(f"[startup] '{import_name}' nicht gefunden – installiere '{pip_spec}' …", flush=True)
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_spec],
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"[startup] '{pip_spec}' erfolgreich installiert.", flush=True)

_ensure_package("qrcode", "qrcode[svg]")
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect
from sqlalchemy import text
from models import db, Team, Mission, Assignment, CaseDoc, RadioLogEntry, ExerciseConfig, PushSubscription, CaseDefinition

# ---------------------------
# Web-Push (VAPID)
# ---------------------------
_VAPID_KEYS_PATH = os.path.join(os.path.dirname(__file__), "instance", "vapid_keys.json")
# Fallback: vapid_keys.json im App-Verzeichnis (Legacy / Entwicklung)
if not os.path.exists(_VAPID_KEYS_PATH):
    _VAPID_KEYS_PATH = os.path.join(os.path.dirname(__file__), "vapid_keys.json")
_VAPID_PRIVATE_PEM = None
_VAPID_PUBLIC_KEY  = None
if os.path.exists(_VAPID_KEYS_PATH):
    with open(_VAPID_KEYS_PATH) as _f:
        _vk = json.load(_f)
        _VAPID_PRIVATE_PEM = _vk["private_pem"]
        _VAPID_PUBLIC_KEY  = _vk["public_key_b64"]


def _send_push(subscription_info: dict, title: str, body: str):
    """Sendet eine Web-Push-Nachricht an ein einzelnes Abonnement."""
    if not _VAPID_PRIVATE_PEM:
        return
    try:
        from pywebpush import webpush, WebPushException
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=_VAPID_PRIVATE_PEM,
            vapid_claims={"sub": "mailto:evt@brk-feucht.local"},
        )
    except Exception:
        pass


def _broadcast_push(evt_name: str, title: str, body: str, app_ctx=None):
    """Sendet Push an alle Abonnements eines EVT."""
    subs = PushSubscription.query.filter_by(evt_name=evt_name).all()
    for sub in subs:
        _send_push(
            {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
            title, body,
        )


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


def _utcnow():
    """UTC now als naive datetime (kompatibel mit bestehender DB)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fmt_dt(dt):
    """ISO 8601 Format mit Z-Suffix, oder None."""
    if dt is None:
        return None
    # Naive datetime → direkt Z anhängen; aware → offset entfernen
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt.isoformat() + "Z"


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
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///einsatzleiter.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # WAL-Modus für SQLite: mehrere gunicorn-Worker können gleichzeitig lesen
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False},
        "pool_pre_ping": True,
    }

    db.init_app(app)

    # SQLite WAL-Modus aktivieren (wichtig für Multi-Worker gunicorn)
    with app.app_context():
        from sqlalchemy import event

        @event.listens_for(db.engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _rec):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.close()

    # Übungs-Falldaten (statisch, aus Übungsleiterunterlagen)
    EXERCISE_CASES = {
        "P1": {
            "schlagwort": "VU (schwer) – Radfahrer vs. PKW",
            "patient": "Lennart Voigt", "alter": 27, "geschlecht": "m",
            "w3w": "///erstes.arbeitswelt.spülmittel", "w3w_alarm": None,
            "lat": 49.377493, "lng": 11.206863,
            "rmi_soll": "211", "sk_soll": "1", "pzc_soll": "211271",
            "abcd_soll": {"A": 1, "B": 2, "C": 4, "D": 2},
            "besonderheit": "Pflichtfall ABCD-Schema (SK1). RD + POL auf Anfahrt.",
        },
        "P2": {
            "schlagwort": "Sturz Skateboard – Handgelenksverletzung",
            "patient": "Elzbieta Szczepaniak", "alter": 19, "geschlecht": "w",
            "patient_alarm": "Lisa Schneider",   # falscher Name in der Alarmierung
            "w3w": "///vorweisen.kanone.möchte", "w3w_alarm": None,
            "lat": 49.377035, "lng": 11.202390,
            "rmi_soll": "272", "sk_soll": "1-3", "pzc_soll": "272191,272192,272193",
            "abcd_soll": {"A": 1, "B": 1, "C": 1, "D": 1},
            "besonderheit": "Name in Alarmierung falsch (Lisa Schneider). Buchstabieren erforderlich.",
        },
        "P3": {
            "schlagwort": "Atemnot – COPD-Exazerbation",
            "patient": "Hakan Yilmaz", "alter": 62, "geschlecht": "m",
            "w3w": "///wunder.untersuchen.lacke",
            "w3w_alarm": "///geiger.kerzen.besonders",
            "lat": 49.379595, "lng": 11.208106,
            "rmi_soll": "312", "sk_soll": "1-3", "pzc_soll": "312621,312622,312623",
            "abcd_soll": {"A": 1, "B": 2, "C": 1, "D": 1},
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
            "rmi_soll": "421", "sk_soll": "1", "pzc_soll": "421721",
            "abcd_soll": {"A": 1, "B": 1, "C": 1, "D": 1},
            "besonderheit": "Stroke-Klinik. Fokus auf PZC / Klinikwahl. Antikoagulation beachten.",
        },
        "P6": {
            "schlagwort": "Brustschmerz – V.a. ACS",
            "patient": "Sabine Lutz", "alter": 56, "geschlecht": "w",
            "w3w": "///obenrum.kranz.wählen", "w3w_alarm": None,
            "lat": 49.375283, "lng": 11.204709,
            "rmi_soll": "331", "sk_soll": "2/3", "pzc_soll": "331562,331563",
            "abcd_soll": {"A": 1, "B": 1, "C": 1, "D": 1},
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
            "ALTER TABLE case_docs ADD COLUMN abcde_schema TEXT",
            "ALTER TABLE case_definitions ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1",
        ]
        with db.engine.connect() as _conn:
            for _sql in _migrations:
                try:
                    _conn.execute(text(_sql))
                    _conn.commit()
                except Exception:
                    pass  # Column already exists
        # CaseDefinition aus EXERCISE_CASES befüllen (nur beim allerersten Start)
        if CaseDefinition.query.count() == 0:
            for i, (cid, cd) in enumerate(EXERCISE_CASES.items()):
                db.session.add(CaseDefinition(
                    id=cid, schlagwort=cd["schlagwort"],
                    szenario=cd.get("szenario"),
                    patient=cd["patient"], patient_alarm=cd.get("patient_alarm"),
                    alter=cd.get("alter"), geschlecht=cd.get("geschlecht"),
                    w3w=cd.get("w3w"), w3w_alarm=cd.get("w3w_alarm"),
                    lat=cd.get("lat"), lng=cd.get("lng"),
                    rmi_soll=cd.get("rmi_soll"), sk_soll=cd.get("sk_soll"),
                    pzc_soll=cd.get("pzc_soll"), besonderheit=cd.get("besonderheit"),
                    abcd_soll_json=json.dumps(cd["abcd_soll"], ensure_ascii=False) if cd.get("abcd_soll") else None,
                    sort_order=i,
                ))
            db.session.flush()

        # CaseDoc-Einträge aus CaseDefinition initialisieren
        for cd_row in CaseDefinition.query.all():
            if db.session.get(CaseDoc, cd_row.id) is None:
                db.session.add(CaseDoc(id=cd_row.id))
        # ExerciseConfig Singleton
        if db.session.get(ExerciseConfig, 1) is None:
            db.session.add(ExerciseConfig(id=1, evt_count=6))
        db.session.commit()

    def _cases_dict(active_only: bool = False):
        """Gibt CaseDefinitions als dict zurück. active_only=True → nur aktive Fälle."""
        q = CaseDefinition.query.order_by(CaseDefinition.sort_order, CaseDefinition.id)
        if active_only:
            q = q.filter(CaseDefinition.active == True)  # noqa: E712
        result = {}
        for cd in q.all():
            result[cd.id] = {
                "schlagwort": cd.schlagwort or "", "szenario": cd.szenario,
                "patient": cd.patient or "", "patient_alarm": cd.patient_alarm,
                "alter": cd.alter, "geschlecht": cd.geschlecht,
                "w3w": cd.w3w, "w3w_alarm": cd.w3w_alarm,
                "lat": cd.lat, "lng": cd.lng,
                "rmi_soll": cd.rmi_soll, "sk_soll": cd.sk_soll, "pzc_soll": cd.pzc_soll,
                "abcd_soll": cd.abcd_soll,
                "besonderheit": cd.besonderheit, "hinweis": cd.hinweis,
                "kein_transport": cd.kein_transport,
                "active": bool(cd.active),
            }
        return result

    @app.get("/health")
    def health_check():
        """Health-Check Endpoint für Monitoring."""
        return jsonify({"status": "ok", "timestamp": _fmt_dt(_utcnow())})

    def _build_dashboard_dict():
        """Baut das Dashboard-Dict (für API und inline-Embedding)."""
        teams_list = Team.query.order_by(Team.updated_at.desc()).all()
        _pending_evts = {
            d.assigned_evt for d in CaseDoc.query.filter(
                CaseDoc.alarm_time.isnot(None),
                CaseDoc.status3_time.is_(None),
                CaseDoc.completed == False  # noqa: E712
            ).all() if d.assigned_evt
        }
        teams_out = []
        for t in teams_list:
            _ident = {t.name, t.callsign} - {None}
            teams_out.append(serialize_team(
                t, include_missions=True,
                pending_alarm=bool(_ident & _pending_evts)
            ))
        missions_out = [serialize_mission(m, include_teams=True)
                        for m in Mission.query.order_by(Mission.updated_at.desc()).all()]
        assigns_out = [serialize_assignment(a)
                       for a in Assignment.query.order_by(Assignment.created_at.desc()).all()]
        docs_out = [serialize_casedoc(d) for d in CaseDoc.query.order_by(CaseDoc.id).all()]
        return {
            "teams": teams_out,
            "missions": missions_out,
            "assignments": assigns_out,
            "casedocs": docs_out,
        }

    @app.get("/api/dashboard")
    def dashboard_data():
        """Alle Dashboard-Daten in einem einzigen Request."""
        return jsonify(_build_dashboard_dict())

    @app.get("/")
    def index():
        import json as _json
        initial_data = _json.dumps(_build_dashboard_dict(), ensure_ascii=False)
        return render_template("index.html", initial_data=initial_data)

    @app.get("/protokoll")
    def protokoll():
        return render_template("protokoll.html", cases=_cases_dict(active_only=True))

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
        # EVT-URL: bei HTTPS ueber HTTP-Port 5080 (automatischer Zertifikat-Setup)
        if proto == "https":
            evt_url = f"http://{lan_ip}:5080/evt"
        else:
            evt_url = f"{proto}://{lan_ip}:{port}/evt"
        return jsonify({
            "ip": lan_ip,
            "port": port,
            "base_url": f"{proto}://{lan_ip}:{port}",
            "evt_url":  evt_url,
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
        return render_template("evt.html", cases=_cases_dict(),
                               startpunkt_w3w=STARTPUNKT_W3W)

    @app.get("/beobachter")
    def beobachter():
        return render_template("beobachter.html")

    @app.get("/api/beobachter")
    def beobachter_data():
        """Daten für die Beobachter-Ansicht: Teams + nur alarmierte Fälle."""
        teams_list = Team.query.order_by(Team.name).all()
        teams_out = [serialize_team(t, include_missions=True) for t in teams_list]

        # Nur Fälle mit alarm_time (alarmiert) zurückgeben
        docs = CaseDoc.query.filter(CaseDoc.alarm_time.isnot(None)).order_by(CaseDoc.id).all()
        cases_out = []
        for d in docs:
            _cd = db.session.get(CaseDefinition, d.id)
            cases_out.append({
                **serialize_casedoc(d),
                "lat": _cd.lat if _cd else None,
                "lng": _cd.lng if _cd else None,
                "schlagwort": (_cd.schlagwort if _cd else "") or "",
                "patient": (_cd.patient if _cd else "") or "",
                "w3w": (_cd.w3w if _cd else "") or "",
            })

        return jsonify({"teams": teams_out, "cases": cases_out})

    @app.get("/api/qrcodes")
    def qr_codes():
        """Generiert QR-Code-Seite für alle konfigurierten EVTs."""
        import io
        import base64
        try:
            import qrcode
            import qrcode.image.svg
        except ImportError as e:
            return jsonify({"error": f"qrcode-Paket fehlt: {e} – pip install 'qrcode[svg]'"}), 500

        try:
            import socket as _socket
            try:
                s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                lan_ip = s.getsockname()[0]
                s.close()
            except Exception:
                lan_ip = "127.0.0.1"
            _cert = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "instance", "cert.pem")
            proto = "https" if os.path.exists(_cert) else "http"
            if proto == "https":
                base = f"http://{lan_ip}:5080"
            else:
                base = f"{proto}://{lan_ip}:5000"

            cfg = db.session.get(ExerciseConfig, 1)
            evt_count = cfg.evt_count if cfg else 6

            def _make_qr(url: str, box_size: int = 8) -> str:
                qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                                   box_size=box_size, border=2)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
                buf = io.BytesIO()
                img.save(buf)
                return base64.b64encode(buf.getvalue()).decode()

            # Einzelner QR für die Beamer-Ansicht (allgemeine EVT-URL, kein Team vorgewählt)
            evt_url = f"{base}/evt"
            evt_qr = {"name": "EVT-App", "url": evt_url, "img_b64": _make_qr(evt_url, box_size=12)}

            # Pro-EVT QR-Codes für den Drucken-Dialog im EL
            codes = []
            for i in range(1, evt_count + 1):
                evt_name = f"EVT {i}"
                url = f"{base}/evt?team={urllib.parse.quote(evt_name)}"
                codes.append({"name": evt_name, "url": url, "img_b64": _make_qr(url)})

            return jsonify({"codes": codes, "evt_qr": evt_qr, "base_url": base})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

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

        _cd_obj = db.session.get(CaseDefinition, active_doc.id) if active_doc else None
        case_meta = _cd_obj.to_dict() if _cd_obj else None
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
        doc = db.get_or_404(CaseDoc, case_id)
        data = request.get_json(force=True)

        for field in ("assigned_evt", "rmi_reported", "sk_reported",
                      "pzc_reported", "abcde_schema", "zielklinik", "notes"):
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

        doc.updated_at = _utcnow()
        _sync_team_from_doc(doc)
        db.session.commit()
        return jsonify(serialize_casedoc(doc))

    @app.post("/api/casedocs/<string:case_id>/stamp")
    def stamp_casedoc(case_id: str):
        """Setzt einen Zeitstempel auf 'jetzt'."""
        doc = db.get_or_404(CaseDoc, case_id)
        data = request.get_json(force=True)
        field = data.get("field")
        allowed = {"alarm_time", "status3_time", "status4_time",
                   "status7_time", "status8_time"}
        if field not in allowed:
            return jsonify({"error": "unknown field"}), 400
        setattr(doc, field, _utcnow())
        doc.updated_at = _utcnow()
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
                ts = _utcnow()
        else:
            ts = _utcnow()

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
        entry = db.get_or_404(RadioLogEntry, entry_id)
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
        now = _utcnow()

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
        """Return exercise case coordinates from CaseDefinition DB."""
        result: dict = {"cases": {}, "startpunkt": None}
        dirty = False
        for cd in CaseDefinition.query.filter(CaseDefinition.active == True).order_by(CaseDefinition.sort_order, CaseDefinition.id).all():  # noqa: E712
            # Always resolve w3w → coordinates (w3w is authoritative source)
            if cd.w3w:
                lat, lng = resolve_w3w(cd.w3w)
                if lat is not None and (cd.lat != lat or cd.lng != lng):
                    cd.lat, cd.lng = lat, lng
                    dirty = True
            result["cases"][cd.id] = {
                "lat": cd.lat, "lng": cd.lng,
                "schlagwort": cd.schlagwort or "",
                "patient": cd.patient or "",
                "w3w": cd.w3w or "",
            }
        if dirty:
            db.session.commit()
        result["startpunkt"] = {"lat": STARTPUNKT_LAT, "lng": STARTPUNKT_LNG, "w3w": STARTPUNKT_W3W}
        return jsonify(result)

    @app.post("/api/exercise/resolve-w3w")
    def exercise_resolve_w3w():
        """Manually trigger w3w → coordinate resolution for all active cases."""
        resolved = 0
        failed = []
        for cd in CaseDefinition.query.filter(CaseDefinition.active == True).all():  # noqa: E712
            if cd.w3w:
                lat, lng = resolve_w3w(cd.w3w)
                if lat is not None:
                    cd.lat, cd.lng = lat, lng
                    resolved += 1
                else:
                    failed.append(cd.id)
        db.session.commit()
        return jsonify({"ok": True, "resolved": resolved, "failed": failed})

    @app.get("/cert")
    def download_cert():
        """Serve self-signed certificate for iOS/Android installation."""
        cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "instance", "cert.pem")
        if not os.path.exists(cert_path):
            return "Kein Zertifikat vorhanden.", 404
        from flask import send_file
        return send_file(cert_path, mimetype="application/x-pem-file",
                         as_attachment=True, download_name="OpManGPT.pem")

    @app.get("/setup")
    def setup_page():
        """Handy-Setup: Zertifikat installieren mit Schritt-fuer-Schritt-Anleitung."""
        back = request.args.get("back", "")
        back_url = "/evt" if back == "evt" else "/"
        back_label = "Zurueck zur EVT-App" if back == "evt" else "Fertig - zur App"
        return ("""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpMan-GPT Handy-Setup</title>
<style>
  body{font-family:-apple-system,sans-serif;max-width:500px;margin:2rem auto;padding:0 1rem;
       background:#0d1117;color:#e6edf3;line-height:1.6}
  h1{font-size:1.3rem;text-align:center}
  .btn{display:block;width:100%;padding:14px;margin:1rem 0;border:none;border-radius:8px;
       font-size:1.1rem;font-weight:600;cursor:pointer;text-align:center;text-decoration:none}
  .btn-dl{background:#2563eb;color:#fff}
  .step{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;margin:1rem 0}
  .step h3{margin:0 0 .5rem;font-size:1rem}
  .step ol{margin:0;padding-left:1.5rem}
  .tab{display:flex;gap:4px;margin-bottom:1rem}
  .tab button{flex:1;padding:10px;border:1px solid #30363d;background:#161b22;color:#e6edf3;
              border-radius:6px;font-size:.95rem;cursor:pointer}
  .tab button.active{background:#2563eb;border-color:#2563eb;color:#fff}
  .panel{display:none}.panel.active{display:block}
  .done{background:#22c55e;color:#000}
</style></head><body>
<h1>OpMan-GPT Handy-Setup</h1>
<p style="text-align:center">GPS braucht ein vertrauenswuerdiges Zertifikat.<br>Einmalig 2 Minuten, dann funktioniert alles.</p>

<div class="tab">
  <button class="active" onclick="show('ios')">iPhone</button>
  <button onclick="show('android')">Android</button>
</div>

<div id="ios" class="panel active">
  <a href="/cert" class="btn btn-dl">1. Zertifikat herunterladen</a>
  <div class="step"><h3>2. Profil installieren</h3>
    <ol>
      <li>Tippe auf "Zulassen" wenn gefragt</li>
      <li>Oeffne <b>Einstellungen</b></li>
      <li>Oben erscheint <b>"Profil geladen"</b> - tippe drauf</li>
      <li>Tippe <b>"Installieren"</b> (2x) und gib deinen Code ein</li>
    </ol>
  </div>
  <div class="step"><h3>3. Zertifikat vertrauen</h3>
    <ol>
      <li><b>Einstellungen</b> → <b>Allgemein</b> → <b>Info</b></li>
      <li>Ganz unten: <b>Zertifikatsvertrauenseinstellungen</b></li>
      <li>Schalter bei <b>"OpMan-GPT Local CA"</b> aktivieren</li>
    </ol>
  </div>
  <a href="{back_url}" class="btn done">{back_label}</a>
</div>

<div id="android" class="panel">
  <a href="/cert" class="btn btn-dl">1. Zertifikat herunterladen</a>
  <div class="step"><h3>2. Zertifikat installieren</h3>
    <ol>
      <li>Oeffne <b>Einstellungen</b> → <b>Sicherheit</b> (oder suche "Zertifikat")</li>
      <li><b>Verschluesselung & Anmeldedaten</b></li>
      <li><b>Zertifikat installieren</b> → <b>CA-Zertifikat</b></li>
      <li>Waehle die heruntergeladene Datei <b>OpManGPT.pem</b></li>
      <li>Bestaetigen</li>
    </ol>
  </div>
  <a href="{back_url}" class="btn done">{back_label}</a>
</div>

<script>
function show(id){
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab button').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}
</script>
</body></html>""".replace("{back_url}", back_url).replace("{back_label}", back_label))

    # ---------------------------
    # Exercise Config
    # ---------------------------
    @app.get("/api/exercise/config")
    def get_exercise_config():
        cfg = db.session.get(ExerciseConfig, 1)
        return jsonify({"evt_count": cfg.evt_count if cfg else 6})

    @app.post("/api/exercise/config")
    def update_exercise_config():
        cfg = db.get_or_404(ExerciseConfig, 1)
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
        """Erstellt Missions aus den Übungsfällen (statische Koordinaten)."""
        created = []
        for cd in CaseDefinition.query.order_by(CaseDefinition.sort_order, CaseDefinition.id).all():
            lat = cd.lat
            lng = cd.lng
            title = f"{cd.id}: {cd.schlagwort}"
            # Nicht doppelt anlegen
            existing = Mission.query.filter_by(title=title).first()
            if existing:
                # Koordinaten nachpflegen, falls sie fehlen oder sich geändert haben
                if existing.lat != lat or existing.lng != lng:
                    existing.lat = lat
                    existing.lng = lng
                    existing.updated_at = _utcnow()
                created.append({"id": existing.id, "title": title, "skipped": True})
                continue
            m = Mission(
                title=title,
                description=cd.besonderheit or None,
                priority=1 if cd.sk_soll == "1" else 3,
                status="offen",
                lat=lat,
                lng=lng,
                updated_at=_utcnow(),
            )
            db.session.add(m)
            db.session.flush()
            created.append({"id": m.id, "title": title, "skipped": False})
        db.session.commit()
        return jsonify({"created": created})

    # ---------------------------
    # Case Editor + Patientenkarten
    # ---------------------------
    @app.get("/cases")
    def cases_list():
        cases = CaseDefinition.query.order_by(CaseDefinition.sort_order, CaseDefinition.id).all()
        return render_template("cases.html", cases=cases)

    @app.get("/cases/new")
    def case_new():
        return render_template("cases.html", cases=[], editing=CaseDefinition(), is_new=True)

    @app.post("/cases/new")
    def case_new_save():
        data = request.form
        cid = (data.get("id") or "").strip().upper()
        if not cid:
            return "Keine Fall-ID angegeben.", 400
        if db.session.get(CaseDefinition, cid):
            return f"Fall '{cid}' existiert bereits.", 400
        _save_case_from_form(CaseDefinition(id=cid), data)
        if db.session.get(CaseDoc, cid) is None:
            db.session.add(CaseDoc(id=cid))
        db.session.commit()
        return redirect("/cases")

    @app.get("/cases/<string:case_id>/edit")
    def case_edit(case_id):
        cd = db.get_or_404(CaseDefinition, case_id)
        cases = CaseDefinition.query.order_by(CaseDefinition.sort_order, CaseDefinition.id).all()
        return render_template("cases.html", cases=cases, editing=cd, is_new=False)

    @app.post("/cases/<string:case_id>/edit")
    def case_edit_save(case_id):
        cd = db.get_or_404(CaseDefinition, case_id)
        _save_case_from_form(cd, request.form)
        db.session.commit()
        return redirect("/cases")

    @app.post("/cases/<string:case_id>/delete")
    def case_delete(case_id):
        cd = db.get_or_404(CaseDefinition, case_id)
        # CaseDoc mitlöschen, damit kein verwaister Datensatz im Protokoll bleibt
        doc = db.session.get(CaseDoc, case_id)
        if doc:
            db.session.delete(doc)
        db.session.delete(cd)
        db.session.commit()
        return redirect("/cases")

    def _save_case_from_form(cd: CaseDefinition, data):
        cd.schlagwort     = data.get("schlagwort", "").strip()
        cd.szenario       = data.get("szenario", "").strip() or None
        cd.patient        = data.get("patient", "").strip()
        cd.patient_alarm  = data.get("patient_alarm", "").strip() or None
        cd.alter          = int(data["alter"]) if data.get("alter") else None
        cd.geschlecht     = data.get("geschlecht", "").strip() or None
        cd.w3w            = data.get("w3w", "").strip() or None
        cd.w3w_alarm      = data.get("w3w_alarm", "").strip() or None
        cd.lat            = float(data["lat"]) if data.get("lat") else None
        cd.lng            = float(data["lng"]) if data.get("lng") else None
        # Always resolve w3w → coordinates (w3w is authoritative source)
        if cd.w3w:
            lat, lng = resolve_w3w(cd.w3w)
            if lat is not None:
                cd.lat = lat
                cd.lng = lng
        cd.rmi_soll       = data.get("rmi_soll", "").strip() or None
        cd.sk_soll        = data.get("sk_soll", "").strip() or None
        cd.pzc_soll       = data.get("pzc_soll", "").strip() or None
        cd.kein_transport = bool(data.get("kein_transport"))
        # ABCD-Soll (4 Einzelfelder → JSON)
        abcd_soll = {}
        for letter in ("A", "B", "C", "D"):
            v = data.get(f"abcd_soll_{letter}", "").strip()
            if v:
                abcd_soll[letter] = int(v)
        cd.abcd_soll_json = json.dumps(abcd_soll, ensure_ascii=False) if abcd_soll else None
        cd.besonderheit   = data.get("besonderheit", "").strip() or None
        cd.hinweis        = data.get("hinweis", "").strip() or None
        cd.sort_order     = int(data["sort_order"]) if data.get("sort_order") else 0
        cd.updated_at     = _utcnow()
        # Vitals (7 Einzelfelder → JSON)
        vitals = {}
        for key in ("RR", "HF", "AF", "SpO2", "Temp", "GCS", "BZ"):
            v = data.get(f"vital_{key}", "").strip()
            if v:
                vitals[key] = v
        cd.vitals_json = json.dumps(vitals, ensure_ascii=False) if vitals else None
        # Befund: eine Zeile = ein Bullet
        befund = [l.strip() for l in data.get("befund", "").splitlines() if l.strip()]
        cd.befund_json = json.dumps(befund, ensure_ascii=False) if befund else None
        # ABCDE
        abcde = {}
        for letter in ("A", "B", "C", "D", "E"):
            v = data.get(f"abcde_{letter}", "").strip()
            if v:
                abcde[letter] = v
        cd.abcde_json = json.dumps(abcde, ensure_ascii=False) if abcde else None
        # SAMPLER
        sampler = {}
        for letter in ("S", "A", "M", "P", "L", "E", "R"):
            v = data.get(f"sampler_{letter}", "").strip()
            if v:
                sampler[letter] = v
        cd.sampler_json = json.dumps(sampler, ensure_ascii=False) if sampler else None
        db.session.add(cd)

    @app.get("/api/cases/meta")
    def cases_meta():
        """Liefert nur AKTIVE Cases – für Protokoll und Karten-Anzeige."""
        return jsonify(_cases_dict(active_only=True))

    @app.get("/api/cases/all")
    def cases_all():
        """Liefert alle Cases inkl. inaktiver – für die EL-Sidebar."""
        return jsonify(_cases_dict(active_only=False))

    @app.patch("/api/cases/<string:case_id>/active")
    def case_toggle_active(case_id: str):
        """Setzt das active-Flag eines Falls (body: {active: true/false})."""
        cd = db.get_or_404(CaseDefinition, case_id)
        data = request.get_json(force=True) or {}
        cd.active = bool(data.get("active", not cd.active))
        db.session.commit()
        return jsonify({"id": cd.id, "active": cd.active})

    @app.get("/api/cases/export")
    def cases_export():
        cases = CaseDefinition.query.order_by(CaseDefinition.sort_order, CaseDefinition.id).all()
        payload = {"version": 1, "cases": [c.to_dict() for c in cases]}
        from flask import Response
        return Response(
            json.dumps(payload, ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=cases_export.json"},
        )

    @app.post("/api/cases/import")
    def cases_import():
        try:
            raw = request.get_json(force=True) or {}
            case_list = raw.get("cases", raw) if isinstance(raw, dict) else raw
            if not isinstance(case_list, list):
                return jsonify({"error": "Erwartet: {\"cases\": [...]} oder direkt [...]"}), 400
            updated, created = 0, 0
            for item in case_list:
                cid = str(item.get("id", "")).strip().upper()
                if not cid:
                    continue
                cd = db.session.get(CaseDefinition, cid)
                if cd is None:
                    cd = CaseDefinition(id=cid)
                    db.session.add(cd)
                    created += 1
                else:
                    updated += 1
                for field in ("schlagwort", "szenario", "patient", "patient_alarm",
                              "alter", "geschlecht", "w3w", "w3w_alarm", "lat", "lng",
                              "rmi_soll", "sk_soll", "pzc_soll", "besonderheit", "hinweis",
                              "kein_transport", "sort_order"):
                    if field in item:
                        setattr(cd, field, item[field])
                if "vitals" in item:
                    cd.vitals_json = json.dumps(item["vitals"], ensure_ascii=False)
                if "befund" in item:
                    cd.befund_json = json.dumps(item["befund"], ensure_ascii=False)
                if "abcde" in item:
                    cd.abcde_json = json.dumps(item["abcde"], ensure_ascii=False)
                if "sampler" in item:
                    cd.sampler_json = json.dumps(item["sampler"], ensure_ascii=False)
                if "abcd_soll" in item:
                    cd.abcd_soll_json = json.dumps(item["abcd_soll"], ensure_ascii=False)
                # Always resolve w3w → coordinates (w3w is authoritative source)
                if cd.w3w:
                    lat, lng = resolve_w3w(cd.w3w)
                    if lat is not None:
                        cd.lat, cd.lng = lat, lng
                cd.updated_at = _utcnow()
                # CaseDoc sicherstellen
                if db.session.get(CaseDoc, cid) is None:
                    db.session.add(CaseDoc(id=cid))
            db.session.commit()
            return jsonify({"ok": True, "created": created, "updated": updated})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/patientenkarten")
    def patientenkarten():
        from datetime import date
        cases = CaseDefinition.query.order_by(CaseDefinition.sort_order, CaseDefinition.id).all()
        return render_template("patientenkarten.html", cases=cases, today=date.today().isoformat())

    @app.get("/patientenkarten/<string:case_id>")
    def patientenkarte_single(case_id):
        from datetime import date
        cd = db.get_or_404(CaseDefinition, case_id)
        return render_template("patientenkarten.html", cases=[cd], today=date.today().isoformat())

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

        # Auto-Name: "EVT 1", "EVT 2", ... wenn kein Name übergeben
        name = (data.get("name") or "").strip()
        if not name:
            existing = Team.query.all()
            used_nums = set()
            for t in existing:
                if t.name.startswith("EVT "):
                    try:
                        used_nums.add(int(t.name[4:]))
                    except ValueError:
                        pass
            n = 1
            while n in used_nums:
                n += 1
            name = f"EVT {n}"

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
            updated_at=_utcnow(),
        )
        db.session.add(team)
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True)), 201

    @app.patch("/api/teams/<int:team_id>")
    def update_team(team_id: int):
        team = db.get_or_404(Team, team_id)
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
                        mission.updated_at = _utcnow()
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
                        setattr(_doc, _field, _utcnow())
                        _doc.updated_at = _utcnow()
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
                        _cfg = db.session.get(ExerciseConfig, 1)
                        _total = _cfg.evt_count if _cfg else 6
                        _globally_done = len(_evts) >= _total
                        if _globally_done or _doc.completed:
                            # Alle EVTs durch ODER manuell als fertig markiert
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
                        _doc.updated_at = _utcnow()
                        # Mission abschließen + Assignment dieses Teams aufheben
                        for _dm in Mission.query.filter(
                            Mission.title.like(f"{_done_case_id}:%")
                        ).all():
                            _dm.status = "abgeschlossen"
                            _dm.updated_at = _utcnow()
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
            team.gps_updated_at = _utcnow()

        team.updated_at = _utcnow()
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True))

    @app.post("/api/teams/<int:team_id>/quittieren")
    def quittieren_team(team_id: int):
        """Quittiert einen Sprechwunsch (S0/S5) und setzt das Team auf den Vorgänger-Status zurück."""
        team = db.get_or_404(Team, team_id)
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
        team.updated_at = _utcnow()

        sw_label = RADIO_STATUS_LABELS.get(sw_status, f"S{sw_status}")
        rs_label  = RADIO_STATUS_LABELS.get(restore_rs, f"S{restore_rs}")
        db.session.add(RadioLogEntry(
            timestamp=_utcnow(),
            sender="FüSt",
            receiver=team.callsign or team.name,
            fms_status=restore_rs,
            case_ref=_case_ref,
            message=f"{sw_label} quittiert – zurück auf FMS {restore_rs} ({rs_label})",
            created_at=_utcnow(),
        ))
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True))

    @app.delete("/api/teams/<int:team_id>")
    def delete_team(team_id: int):
        team = db.get_or_404(Team, team_id)
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
        now = _utcnow()

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
        team = db.get_or_404(Team, team_id)
        team.test_alarm_at   = None
        team.test_alarm_text = None
        team.updated_at      = _utcnow()
        db.session.commit()
        return jsonify({"ok": True})

    # ---------------------------
    # Web-Push Subscriptions
    # ---------------------------
    @app.get("/api/push/vapid-key")
    def get_vapid_key():
        return jsonify({"publicKey": _VAPID_PUBLIC_KEY or ""})

    @app.post("/api/push/subscribe")
    def push_subscribe():
        data = request.get_json(force=True)
        evt_name = (data.get("evt_name") or "").strip()
        sub = data.get("subscription") or {}
        endpoint = sub.get("endpoint") or ""
        keys = sub.get("keys") or {}
        p256dh = keys.get("p256dh") or ""
        auth = keys.get("auth") or ""
        if not evt_name or not endpoint or not p256dh or not auth:
            return jsonify({"error": "missing fields"}), 400
        # Upsert: vorhandenes Abo aktualisieren oder neu anlegen
        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if existing:
            existing.evt_name = evt_name
            existing.p256dh = p256dh
            existing.auth = auth
        else:
            db.session.add(PushSubscription(
                evt_name=evt_name, endpoint=endpoint, p256dh=p256dh, auth=auth))
        db.session.commit()
        return jsonify({"ok": True}), 201

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
            updated_at=_utcnow(),
        )
        db.session.add(mission)
        db.session.commit()
        return jsonify(serialize_mission(mission, include_teams=True)), 201

    @app.patch("/api/missions/<int:mission_id>")
    def update_mission(mission_id: int):
        mission = db.get_or_404(Mission, mission_id)
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

        mission.updated_at = _utcnow()
        db.session.commit()
        return jsonify(serialize_mission(mission, include_teams=True))

    @app.delete("/api/missions/<int:mission_id>")
    def delete_mission(mission_id: int):
        mission = db.get_or_404(Mission, mission_id)
        # Wenn Mission einem Übungsfall zugeordnet war (Titel "P1: …"),
        # assigned_evt im CaseDoc zurücksetzen damit die Protokoll-Seite stimmt.
        if mission.title:
            case_id = mission.title.split(':')[0].strip()
            doc = db.session.get(CaseDoc, case_id)
            if doc and doc.assigned_evt:
                doc.assigned_evt = None
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

        team = db.get_or_404(Team, int(team_id))
        mission = db.get_or_404(Mission, int(mission_id))

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
            mission.updated_at = _utcnow()

        # Team: nach Zuweisung optional Availability umstellen
        # (damit es nicht weiter als verfügbar angeboten wird)
        team.availability = "bedingt"
        team.updated_at = _utcnow()

        # CaseDoc alarmieren: Mission-Titel hat Format "P1: Schlagwort"
        _parts = mission.title.split(":", 1)
        _mission_case_id = _parts[0].strip() if len(_parts) >= 2 else None
        if _mission_case_id:
            _cdoc = db.session.get(CaseDoc, _mission_case_id)
            if _cdoc and not _cdoc.alarm_time and not _cdoc.completed:
                _cdoc.assigned_evt = team.name
                _cdoc.alarm_time   = _utcnow()
                _cdoc.updated_at   = _utcnow()

                # Web-Push an das zugewiesene EVT senden
                _meta_cd = db.session.get(CaseDefinition, _mission_case_id)
                _push_body = (_meta_cd.schlagwort if _meta_cd else "") or ""
                _broadcast_push(
                    team.name,
                    f"NEUER EINSATZ – {_mission_case_id}",
                    _push_body,
                )

        db.session.commit()
        return jsonify(serialize_assignment(a)), 201

    @app.delete("/api/assignments/<int:assignment_id>")
    def delete_assignment(assignment_id: int):
        a = db.get_or_404(Assignment, assignment_id)

        team = a.team  # Team merken bevor wir löschen
        db.session.delete(a)
        db.session.commit()

        # Prüfen ob Team noch irgendeinem Einsatz zugewiesen ist
        still_assigned = Assignment.query.filter_by(team_id=team.id).first() is not None

        if not still_assigned:
            # Team wieder verfügbar machen
            team.availability = "verfügbar"
            team.updated_at = _utcnow()
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
        timestamp=_utcnow(),
        sender=name,
        receiver="FüSt",
        fms_status=rs,
        case_ref=case_ref,
        message=f"FMS {rs} – {label}",
        created_at=_utcnow(),
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
    team.updated_at = _utcnow()
    _auto_log(team, rs, case_ref=doc.id)


# ---------------------------
# Serialization
# ---------------------------
def serialize_casedoc(d: CaseDoc):
    return {
        "id":            d.id,
        "assigned_evt":  d.assigned_evt,
        "alarm_time":    _fmt_dt(d.alarm_time),
        "status3_time":  _fmt_dt(d.status3_time),
        "status4_time":  _fmt_dt(d.status4_time),
        "status7_time":  _fmt_dt(d.status7_time),
        "status8_time":  _fmt_dt(d.status8_time),
        "rmi_reported":  d.rmi_reported,
        "sk_reported":   d.sk_reported,
        "pzc_reported":  d.pzc_reported,
        "abcde_schema":  d.abcde_schema,
        "zielklinik":    d.zielklinik,
        "notes":         d.notes,
        "completed":     d.completed,
        "completed_evts": json.loads(getattr(d, "completed_evts", None) or "[]"),
        "updated_at":    _fmt_dt(d.updated_at),
    }


def serialize_logentry(e: RadioLogEntry):
    return {
        "id":         e.id,
        "timestamp":  _fmt_dt(e.timestamp),
        "sender":     e.sender,
        "receiver":   e.receiver,
        "fms_status": e.fms_status,
        "case_ref":   e.case_ref,
        "message":    e.message,
        "created_at": _fmt_dt(e.created_at),
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
        "gps_updated_at":  _fmt_dt(t.gps_updated_at),
        "test_alarm_at":   _fmt_dt(t.test_alarm_at),
        "test_alarm_text": t.test_alarm_text,
        "updated_at": _fmt_dt(t.updated_at),
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
        "updated_at": _fmt_dt(m.updated_at),
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
        "created_at": _fmt_dt(a.created_at),
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
    import os as _os, socket as _socket, subprocess as _subprocess, sys as _sys

    _INST = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "instance")
    _CERT = _os.path.join(_INST, "cert.pem")
    _KEY  = _os.path.join(_INST, "key.pem")

    def _lan_ip():
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _make_cert():
        if _os.path.exists(_CERT) and _os.path.exists(_KEY):
            return True
        lip = _lan_ip()
        _os.makedirs(_INST, exist_ok=True)
        print(f"Generiere SSL-Zertifikat fuer {lip} ...")
        # cryptography auto-installieren falls noetig
        try:
            import cryptography  # noqa: F401
        except ImportError:
            print("  'cryptography' nicht installiert - installiere automatisch ...")
            r = _subprocess.run([_sys.executable, "-m", "pip", "install", "cryptography"],
                                capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  Installation fehlgeschlagen. Starte ohne HTTPS.")
                return False
            print("  cryptography erfolgreich installiert.")
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime, ipaddress
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            san = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
            if lip != "127.0.0.1":
                san.append(x509.IPAddress(ipaddress.ip_address(lip)))
            # CA=True damit Chrome das Zertifikat als Root-CA akzeptiert
            cert = (x509.CertificateBuilder()
                    .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "OpMan-GPT Local CA")]))
                    .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "OpMan-GPT Local CA")]))
                    .public_key(key.public_key())
                    .serial_number(x509.random_serial_number())
                    .not_valid_before(datetime.datetime.now(datetime.UTC))
                    .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=825))
                    .add_extension(x509.SubjectAlternativeName(san), critical=False)
                    .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                    .sign(key, hashes.SHA256()))
            with open(_KEY, "wb") as f:
                f.write(key.private_bytes(serialization.Encoding.PEM,
                        serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
            with open(_CERT, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            print(f"  Zertifikat erstellt: {_CERT}")

            # Windows: Zertifikat automatisch als vertrauenswuerdige Root-CA installieren
            if _sys.platform == "win32":
                print("  Installiere Zertifikat in Windows-Vertrauensspeicher ...")
                print("  (Es erscheint evtl. eine Admin-Abfrage - bitte bestaetigen)")
                r = _subprocess.run(
                    ["certutil", "-addstore", "Root", _CERT],
                    capture_output=True, text=True,
                )
                if r.returncode == 0:
                    print("  Zertifikat als vertrauenswuerdig installiert!")
                else:
                    print(f"  Auto-Installation fehlgeschlagen (braucht Admin-Rechte).")
                    print(f"  Manuell: certutil -addstore Root \"{_CERT}\"")

            return True
        except Exception as e:
            print(f"  Zertifikat-Erstellung fehlgeschlagen: {e}")
            return False

    app = create_app()
    lip = _lan_ip()
    has_cert = _make_cert()

    proto = "https" if has_cert else "http"
    print()
    print("=" * 60)
    print(f"  OpMan-GPT startet mit {proto.upper()}")
    print(f"  {proto}://{lip}:5000        <- LAN (Handy)")
    print(f"  {proto}://localhost:5000        <- lokal")
    if has_cert:
        print("  Beim ersten Oeffnen: Sicherheitswarnung -> 'Trotzdem oeffnen'")
    else:
        print("  !  GPS funktioniert NICHT ueber HTTP auf iOS/Android!")
    print("=" * 60)
    print()

    ssl_ctx = (_CERT, _KEY) if has_cert else None

    # HTTP-Server auf Port 5080: EVT-Einstieg fuer Handys
    # Automatischer Flow: /evt → Zertifikat installieren → weiter zu HTTPS
    if has_cert:
        import threading
        from flask import Flask as _Flask, redirect as _redirect

        cert_app = _Flask(__name__)
        _HTTPS_EVT = f"https://{lip}:5000/evt"

        @cert_app.get("/")
        def _cert_landing():
            return _redirect("/evt")

        @cert_app.get("/evt")
        def _cert_evt():
            """EVT-Einstieg: Zertifikat + Anleitung + Weiter-Button in einem."""
            return ("""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVT Setup</title>
<style>
  body{font-family:-apple-system,sans-serif;max-width:500px;margin:0 auto;padding:1.5rem 1rem;
       background:#0b1220;color:#e7eefc;line-height:1.6}
  h1{font-size:1.3rem;text-align:center;margin-bottom:.5rem}
  .sub{text-align:center;color:#a6b3d1;font-size:.9rem;margin-bottom:1.5rem}
  .btn{display:block;width:100%;padding:14px;margin:.8rem 0;border:none;border-radius:8px;
       font-size:1.1rem;font-weight:600;cursor:pointer;text-align:center;text-decoration:none;color:#fff}
  .dl{background:#2563eb}
  .go{background:#22c55e;color:#000;font-size:1.2rem;margin-top:1.5rem}
  .step{background:#111b2e;border:1px solid #223152;border-radius:8px;padding:.8rem 1rem;margin:.8rem 0}
  .step b{color:#4ea1ff}
  .num{display:inline-block;background:#2563eb;color:#fff;width:24px;height:24px;border-radius:50%;
       text-align:center;font-size:.85rem;line-height:24px;margin-right:6px}
  .tab{display:flex;gap:4px;margin-bottom:.8rem}
  .tab button{flex:1;padding:10px;border:1px solid #223152;background:#111b2e;color:#e7eefc;
              border-radius:6px;font-size:.95rem;cursor:pointer}
  .tab button.active{background:#2563eb;border-color:#2563eb}
  .panel{display:none}.panel.active{display:block}
</style></head><body>
<h1>EVT-App Setup</h1>
<p class="sub">Einmalig: Zertifikat installieren, damit GPS funktioniert.</p>

<a href="/cert" class="btn dl"><span class="num">1</span> Zertifikat herunterladen</a>

<div class="tab">
  <button class="active" onclick="show('ios')">iPhone</button>
  <button onclick="show('android')">Android</button>
</div>

<div id="ios" class="panel active">
  <div class="step">
    <span class="num">2</span> <b>Einstellungen</b> oeffnen &rarr; oben auf <b>"Profil geladen"</b> tippen &rarr; <b>Installieren</b>
  </div>
  <div class="step">
    <span class="num">3</span> <b>Einstellungen</b> &rarr; <b>Allgemein</b> &rarr; <b>Info</b> &rarr; ganz unten <b>Zertifikatsvertrauenseinstellungen</b> &rarr; Schalter <b>aktivieren</b>
  </div>
</div>

<div id="android" class="panel">
  <div class="step">
    <span class="num">2</span> <b>Einstellungen</b> &rarr; Suche <b>"Zertifikat"</b> &rarr; <b>CA-Zertifikat installieren</b> &rarr; Datei waehlen &rarr; Bestaetigen
  </div>
</div>

<a href="__HTTPS_EVT__" class="btn go"><span class="num">&#10003;</span> Fertig &ndash; EVT-App oeffnen</a>

<script>
function show(id){
  document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.tab button').forEach(function(b){b.classList.remove('active')});
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}
</script>
</body></html>""".replace("__HTTPS_EVT__", _HTTPS_EVT))

        @cert_app.get("/cert")
        def _cert_download():
            from flask import send_file as _sf
            return _sf(_CERT, mimetype="application/x-pem-file",
                       as_attachment=True, download_name="OpManGPT.pem")

        def _run_cert_server():
            cert_app.run(host="0.0.0.0", port=5080, debug=False, threaded=True)

        t = threading.Thread(target=_run_cert_server, daemon=True)
        t.start()
        print(f"  EVT-App (Handy): http://{lip}:5080/evt")
        print()

    app.run(host="0.0.0.0", port=5000, debug=False,
            ssl_context=ssl_ctx, threaded=True)
