from __future__ import annotations

from datetime import datetime
from flask import Flask, render_template, request, jsonify
from models import db, Team, Mission, Assignment

# ---------------------------
# Funkstatus (Code -> Text)
# ---------------------------
RADIO_STATUS_LABELS: dict[int, str] = {
    1:  "Frei auf Funk",
    2:  "Frei auf Wache",
    3:  "Auf Anfahrt",
    4:  "Am Einsatzort",
    5:  "Sprechwunsch",
    6:  "nicht Einsatzbereit",
    7:  "gebunden",
    8:  "Bedingt Einsatzbereit",
    9:  "Fremdanmeldung",
    0:  "prio. Sprechwunsch",
}

# ---------------------------
# Verfügbarkeit (Disposition)
# ---------------------------
ALLOWED_AVAILABILITY = {"verfügbar", "bedingt", "nicht_verfügbar"}

# Optional (empfohlen): welche Funkstatus gelten als "disponierbar"?
# Wenn du ALLE "availability=verfügbar" zulassen willst, setze DISPATCHABLE... = None
DISPATCHABLE_RADIO_STATUSES: set[int] | None = {1, 2}  # frei auf Funk / frei auf Wache


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///einsatzleiter.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def index():
        return render_template("index.html")

    # ---------------------------
    # Teams
    # ---------------------------
    @app.get("/api/teams")
    def list_teams():
        teams = Team.query.order_by(Team.updated_at.desc()).all()
        return jsonify([serialize_team(t, include_missions=True) for t in teams])

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

        if "radio_status" in data:
            rs = int(data["radio_status"])
            if rs not in RADIO_STATUS_LABELS:
                return jsonify({"error": "radio_status not allowed"}), 400
            team.radio_status = rs

        if "color" in data:
            team.color = (data["color"] or team.color).strip() or team.color

        if "lat" in data:
            team.lat = data["lat"]
        if "lng" in data:
            team.lng = data["lng"]

        team.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(serialize_team(team, include_missions=True))

    @app.delete("/api/teams/<int:team_id>")
    def delete_team(team_id: int):
        team = Team.query.get_or_404(team_id)
        db.session.delete(team)
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
# Serialization
# ---------------------------
def serialize_team(t: Team, include_missions: bool = False):
    payload = {
        "id": t.id,
        "name": t.name,
        "callsign": t.callsign,
        "availability": t.availability,
        "radio_status": t.radio_status,
        "radio_status_label": RADIO_STATUS_LABELS.get(t.radio_status, "unbekannt"),
        "color": t.color,
        "lat": t.lat,
        "lng": t.lng,
        "updated_at": t.updated_at.isoformat() + "Z",
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
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
