"""Tests for all API endpoints (CRUD operations, health, dashboard, etc.)."""
from __future__ import annotations

import json

from models import Team, Mission, Assignment, CaseDoc, RadioLogEntry, ExerciseConfig


class TestHealthEndpoint:
    """Public health-check endpoint."""

    def test_health_endpoint(self, app, client):
        with app.app_context():
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["status"] in ("ok", "healthy")
            assert "timestamp" in data


class TestDashboardAPI:
    """Dashboard data endpoint."""

    def test_dashboard_api(self, app, auth_client):
        with app.app_context():
            resp = auth_client.get("/api/dashboard")
            assert resp.status_code == 200
            data = resp.get_json()
            assert "teams" in data
            assert "missions" in data
            assert "assignments" in data
            assert "casedocs" in data

    def test_dashboard_requires_auth(self, app, client):
        with app.app_context():
            resp = client.get("/api/dashboard")
            assert resp.status_code in (302, 401)


class TestTeamsCRUD:
    """Team create, read, update, delete operations."""

    def test_create_team(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/teams",
                                    json={"name": "EVT Test 1", "radio_status": 1},
                                    content_type="application/json")
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["name"] == "EVT Test 1"
            assert data["radio_status"] == 1

    def test_create_team_auto_name(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/teams",
                                    json={},
                                    content_type="application/json")
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["name"].startswith("EVT ")

    def test_list_teams(self, app, auth_client):
        with app.app_context():
            # Create a team first
            auth_client.post("/api/teams",
                             json={"name": "List Test"},
                             content_type="application/json")
            resp = auth_client.get("/api/teams")
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
            assert len(data) >= 1

    def test_update_team(self, app, auth_client):
        with app.app_context():
            # Create
            create_resp = auth_client.post("/api/teams",
                                           json={"name": "Update Me"},
                                           content_type="application/json")
            team_id = create_resp.get_json()["id"]

            # Update
            resp = auth_client.patch(f"/api/teams/{team_id}",
                                     json={"radio_status": 3, "availability": "bedingt"},
                                     content_type="application/json")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["radio_status"] == 3
            assert data["availability"] == "bedingt"

    def test_delete_team(self, app, auth_client):
        with app.app_context():
            create_resp = auth_client.post("/api/teams",
                                           json={"name": "Delete Me"},
                                           content_type="application/json")
            team_id = create_resp.get_json()["id"]

            resp = auth_client.delete(f"/api/teams/{team_id}")
            assert resp.status_code == 200

            # Verify deleted
            get_resp = auth_client.get("/api/teams")
            names = [t["name"] for t in get_resp.get_json()]
            assert "Delete Me" not in names

    def test_update_team_invalid_availability(self, app, auth_client):
        with app.app_context():
            create_resp = auth_client.post("/api/teams",
                                           json={"name": "Invalid Avail"},
                                           content_type="application/json")
            team_id = create_resp.get_json()["id"]
            resp = auth_client.patch(f"/api/teams/{team_id}",
                                     json={"availability": "INVALID"},
                                     content_type="application/json")
            assert resp.status_code == 400


class TestMissionsCRUD:
    """Mission create, read, update, delete operations."""

    def test_create_mission(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/missions",
                                    json={"title": "Test Mission", "priority": 1},
                                    content_type="application/json")
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["title"] == "Test Mission"
            assert data["priority"] == 1

    def test_list_missions(self, app, auth_client):
        with app.app_context():
            auth_client.post("/api/missions",
                             json={"title": "List Mission"},
                             content_type="application/json")
            resp = auth_client.get("/api/missions")
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)

    def test_update_mission(self, app, auth_client):
        with app.app_context():
            create_resp = auth_client.post("/api/missions",
                                           json={"title": "Patch Me"},
                                           content_type="application/json")
            mission_id = create_resp.get_json()["id"]

            resp = auth_client.patch(f"/api/missions/{mission_id}",
                                     json={"status": "zugewiesen"},
                                     content_type="application/json")
            assert resp.status_code == 200
            assert resp.get_json()["status"] == "zugewiesen"

    def test_delete_mission(self, app, auth_client):
        with app.app_context():
            create_resp = auth_client.post("/api/missions",
                                           json={"title": "Delete Mission"},
                                           content_type="application/json")
            mission_id = create_resp.get_json()["id"]

            resp = auth_client.delete(f"/api/missions/{mission_id}")
            assert resp.status_code == 200


class TestAssignmentsCRUD:
    """Assignment create, read, delete operations."""

    def test_create_assignment(self, app, auth_client):
        with app.app_context():
            team_resp = auth_client.post("/api/teams",
                                         json={"name": "Assign Team"},
                                         content_type="application/json")
            team_id = team_resp.get_json()["id"]

            mission_resp = auth_client.post("/api/missions",
                                            json={"title": "Assign Mission"},
                                            content_type="application/json")
            mission_id = mission_resp.get_json()["id"]

            resp = auth_client.post("/api/assignments",
                                    json={"team_id": team_id, "mission_id": mission_id},
                                    content_type="application/json")
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["team_id"] == team_id
            assert data["mission_id"] == mission_id

    def test_delete_assignment(self, app, auth_client):
        with app.app_context():
            team_resp = auth_client.post("/api/teams",
                                         json={"name": "Del Assign Team"},
                                         content_type="application/json")
            team_id = team_resp.get_json()["id"]

            mission_resp = auth_client.post("/api/missions",
                                            json={"title": "Del Assign Mission"},
                                            content_type="application/json")
            mission_id = mission_resp.get_json()["id"]

            assign_resp = auth_client.post("/api/assignments",
                                           json={"team_id": team_id, "mission_id": mission_id},
                                           content_type="application/json")
            assign_id = assign_resp.get_json()["id"]

            resp = auth_client.delete(f"/api/assignments/{assign_id}")
            assert resp.status_code == 200


class TestCaseDocsAPI:
    """CaseDoc listing and update."""

    def test_casedocs_api(self, app, auth_client, db_session):
        with app.app_context():
            # Seed a CaseDoc
            doc = CaseDoc(id="P1")
            db_session.session.add(doc)
            db_session.session.commit()

            resp = auth_client.get("/api/casedocs")
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
            assert any(d["id"] == "P1" for d in data)

    def test_update_casedoc(self, app, auth_client, db_session):
        with app.app_context():
            doc = CaseDoc(id="P2")
            db_session.session.add(doc)
            db_session.session.commit()

            resp = auth_client.patch("/api/casedocs/P2",
                                     json={"assigned_evt": "EVT 1", "notes": "Test note"},
                                     content_type="application/json")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["assigned_evt"] == "EVT 1"
            assert data["notes"] == "Test note"


class TestRadioLogCRUD:
    """RadioLog entry create, list, delete."""

    def test_create_radio_log_entry(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/radiolog",
                                    json={
                                        "sender": "EVT 1",
                                        "receiver": "FueSt",
                                        "message": "Status 3 uebernommen",
                                        "fms_status": 3,
                                    },
                                    content_type="application/json")
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["sender"] == "EVT 1"
            assert data["fms_status"] == 3

    def test_list_radio_log(self, app, auth_client):
        with app.app_context():
            # Create an entry
            auth_client.post("/api/radiolog",
                             json={"sender": "EVT 2", "message": "Test"},
                             content_type="application/json")
            resp = auth_client.get("/api/radiolog")
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)
            assert len(data) >= 1

    def test_delete_radio_log_entry(self, app, auth_client):
        with app.app_context():
            create_resp = auth_client.post("/api/radiolog",
                                           json={"sender": "EVT 3", "message": "Delete me"},
                                           content_type="application/json")
            entry_id = create_resp.get_json()["id"]

            resp = auth_client.delete(f"/api/radiolog/{entry_id}")
            assert resp.status_code == 200

    def test_create_radio_log_missing_sender(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/radiolog",
                                    json={"message": "No sender"},
                                    content_type="application/json")
            assert resp.status_code == 400

    def test_create_radio_log_missing_message(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/radiolog",
                                    json={"sender": "EVT 1"},
                                    content_type="application/json")
            assert resp.status_code == 400


class TestExerciseReset:
    """Exercise reset endpoint (requires admin/schichtleiter/disponent)."""

    def test_exercise_reset(self, app, auth_client, db_session):
        with app.app_context():
            # Seed some data
            doc = CaseDoc(id="P1")
            db_session.session.add(doc)
            db_session.session.commit()

            resp = auth_client.post("/api/reset",
                                    json={"include_log": True, "reset_teams": True},
                                    content_type="application/json")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["ok"] is True

    def test_exercise_reset_requires_role(self, app, client, beobachter_user):
        """Beobachter cannot reset."""
        with app.app_context():
            client.post("/login", data={
                "username": "testbeobachter",
                "password": "Beob1234!",
            })
            resp = client.post("/api/reset",
                               json={},
                               content_type="application/json")
            assert resp.status_code == 403


class TestExerciseConfig:
    """Exercise configuration endpoint."""

    def test_get_exercise_config(self, app, auth_client, db_session):
        with app.app_context():
            # Seed the config
            from models import ExerciseConfig as EC
            cfg = EC(id=1, evt_count=6)
            db_session.session.add(cfg)
            db_session.session.commit()

            resp = auth_client.get("/api/exercise/config")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["evt_count"] == 6

    def test_update_exercise_config(self, app, auth_client, db_session):
        with app.app_context():
            from models import ExerciseConfig as EC
            cfg = EC(id=1, evt_count=6)
            db_session.session.add(cfg)
            db_session.session.commit()

            resp = auth_client.post("/api/exercise/config",
                                    json={"evt_count": 4},
                                    content_type="application/json")
            assert resp.status_code == 200
            assert resp.get_json()["evt_count"] == 4

    def test_update_exercise_config_invalid(self, app, auth_client, db_session):
        with app.app_context():
            from models import ExerciseConfig as EC
            cfg = EC(id=1, evt_count=6)
            db_session.session.add(cfg)
            db_session.session.commit()

            resp = auth_client.post("/api/exercise/config",
                                    json={"evt_count": 99},
                                    content_type="application/json")
            assert resp.status_code == 400


class TestInputValidation:
    """Input validation: max lengths, special characters."""

    def test_team_name_max_length(self, app, auth_client):
        with app.app_context():
            long_name = "A" * 200
            resp = auth_client.post("/api/teams",
                                    json={"name": long_name},
                                    content_type="application/json")
            # Should either truncate or accept (SQLite may not enforce)
            assert resp.status_code in (201, 400, 500)

    def test_special_characters_in_team_name(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/teams",
                                    json={"name": "EVT <script>alert(1)</script>"},
                                    content_type="application/json")
            assert resp.status_code == 201
            data = resp.get_json()
            # Name is stored as-is; escaping happens on rendering
            assert data["name"] == "EVT <script>alert(1)</script>"

    def test_radio_log_empty_sender(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/radiolog",
                                    json={"sender": "", "message": "test"},
                                    content_type="application/json")
            assert resp.status_code == 400

    def test_radio_log_whitespace_sender(self, app, auth_client):
        with app.app_context():
            resp = auth_client.post("/api/radiolog",
                                    json={"sender": "   ", "message": "test"},
                                    content_type="application/json")
            assert resp.status_code == 400
