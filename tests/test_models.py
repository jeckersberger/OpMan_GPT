"""Tests for database models (User, Team, AuditLog, CaseDefinition)."""
from __future__ import annotations

import json

from models import (
    User, AuditLog, Team, Mission, Assignment, CaseDoc,
    CaseDefinition, ROLE_HIERARCHY, ROLES,
)


class TestUserPasswordHashing:
    """Verify bcrypt password hashing and verification."""

    def test_set_and_check_password(self, app, db_session):
        with app.app_context():
            user = User(username="hashtest", role="beobachter")
            user.set_password("Secure!Pass1")
            db_session.session.add(user)
            db_session.session.commit()

            assert user.password_hash is not None
            assert user.password_hash != "Secure!Pass1"  # must be hashed
            assert user.check_password("Secure!Pass1") is True

    def test_wrong_password_returns_false(self, app, db_session):
        with app.app_context():
            user = User(username="hashtest2", role="beobachter")
            user.set_password("CorrectPassword1")
            db_session.session.add(user)
            db_session.session.commit()

            assert user.check_password("WrongPassword") is False

    def test_empty_hash_returns_false(self, app, db_session):
        with app.app_context():
            user = User(username="nohash", role="beobachter", password_hash="")
            db_session.session.add(user)
            db_session.session.commit()

            assert user.check_password("anything") is False


class TestUserRoleHierarchy:
    """Verify role hierarchy and has_role / has_any_role logic."""

    def test_admin_has_highest_level(self):
        assert ROLE_HIERARCHY["admin"] == 100

    def test_beobachter_has_lowest_level(self):
        assert ROLE_HIERARCHY["beobachter"] == 10

    def test_hierarchy_ordering(self):
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["schichtleiter"]
        assert ROLE_HIERARCHY["schichtleiter"] > ROLE_HIERARCHY["disponent"]
        assert ROLE_HIERARCHY["disponent"] > ROLE_HIERARCHY["evt_operator"]
        assert ROLE_HIERARCHY["evt_operator"] > ROLE_HIERARCHY["beobachter"]


class TestUserHasRole:
    """Test User.has_role() and User.has_any_role() methods."""

    def test_admin_has_all_roles(self, app, db_session):
        with app.app_context():
            user = User(username="admin_hr", role="admin")
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()

            for role_name in ROLES:
                assert user.has_role(role_name) is True, f"Admin should have role '{role_name}'"

    def test_beobachter_cannot_access_admin(self, app, db_session):
        with app.app_context():
            user = User(username="beob_hr", role="beobachter")
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()

            assert user.has_role("admin") is False
            assert user.has_role("disponent") is False

    def test_beobachter_has_own_role(self, app, db_session):
        with app.app_context():
            user = User(username="beob_own", role="beobachter")
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()

            assert user.has_role("beobachter") is True

    def test_has_any_role_with_matching_role(self, app, db_session):
        with app.app_context():
            user = User(username="dispo_any", role="disponent")
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()

            assert user.has_any_role("disponent", "admin") is True

    def test_has_any_role_via_hierarchy(self, app, db_session):
        with app.app_context():
            user = User(username="admin_any", role="admin")
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()

            # admin (100) >= disponent (60)
            assert user.has_any_role("disponent") is True


class TestAuditLogCreation:
    """Test AuditLog model can be created and persisted."""

    def test_create_audit_entry(self, app, db_session):
        from datetime import datetime
        with app.app_context():
            entry = AuditLog(
                timestamp=datetime.utcnow(),
                action="TEST_ACTION",
                resource="test_resource",
                resource_id="42",
                details="Test audit log entry",
                ip_address="127.0.0.1",
            )
            db_session.session.add(entry)
            db_session.session.commit()

            saved = AuditLog.query.first()
            assert saved is not None
            assert saved.action == "TEST_ACTION"
            assert saved.resource == "test_resource"
            assert saved.resource_id == "42"


class TestCaseDefinitionToDict:
    """Test CaseDefinition.to_dict() serialization."""

    def test_to_dict_contains_all_keys(self, app, db_session):
        with app.app_context():
            cd = CaseDefinition(
                id="T1",
                schlagwort="Test case",
                patient="Max Mustermann",
                alter=30,
                geschlecht="m",
                lat=49.37,
                lng=11.20,
                rmi_soll="211",
                sk_soll="1",
                pzc_soll="211271",
                kein_transport=False,
                vitals_json=json.dumps({"RR": "120/80", "HF": "72"}),
                befund_json=json.dumps(["Befund A", "Befund B"]),
                abcde_json=json.dumps({"A": "frei", "B": "normal"}),
                sampler_json=json.dumps({"S": "Symptome", "A": "Allergien"}),
            )
            db_session.session.add(cd)
            db_session.session.commit()

            d = cd.to_dict()
            assert d["id"] == "T1"
            assert d["schlagwort"] == "Test case"
            assert d["patient"] == "Max Mustermann"
            assert d["alter"] == 30
            assert d["geschlecht"] == "m"
            assert d["lat"] == 49.37
            assert d["lng"] == 11.20
            assert d["vitals"]["RR"] == "120/80"
            assert len(d["befund"]) == 2
            assert d["abcde"]["A"] == "frei"
            assert d["sampler"]["S"] == "Symptome"
            assert d["kein_transport"] is False

    def test_to_dict_with_empty_json(self, app, db_session):
        with app.app_context():
            cd = CaseDefinition(id="T2", schlagwort="Empty", patient="Nobody")
            db_session.session.add(cd)
            db_session.session.commit()

            d = cd.to_dict()
            assert d["vitals"] == {}
            assert d["befund"] == []
            assert d["abcde"] == {}
            assert d["sampler"] == {}


class TestTeamCreation:
    """Test Team model creation and defaults."""

    def test_create_team_with_defaults(self, app, db_session):
        with app.app_context():
            team = Team(name="EVT 1")
            db_session.session.add(team)
            db_session.session.commit()

            saved = Team.query.first()
            assert saved is not None
            assert saved.name == "EVT 1"
            assert saved.radio_status == 1
            assert saved.availability == "verfügbar"
            assert saved.color == "#4ea1ff"
            assert saved.radio_group == "regelfunk"

    def test_create_team_with_custom_values(self, app, db_session):
        with app.app_context():
            team = Team(
                name="RTW 71/1",
                callsign="Florian Nuernberg 71/1",
                radio_status=2,
                availability="bedingt",
                color="#ff0000",
                lat=49.45,
                lng=11.08,
            )
            db_session.session.add(team)
            db_session.session.commit()

            saved = Team.query.first()
            assert saved.name == "RTW 71/1"
            assert saved.callsign == "Florian Nuernberg 71/1"
            assert saved.radio_status == 2
            assert saved.availability == "bedingt"
            assert saved.lat == 49.45


class TestUserIsActive:
    """Test the User.is_active property (combines is_active_user and is_locked)."""

    def test_active_unlocked_user(self, app, db_session):
        with app.app_context():
            user = User(username="active1", role="beobachter",
                        is_active_user=True, is_locked=False)
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()
            assert user.is_active is True

    def test_locked_user_is_not_active(self, app, db_session):
        with app.app_context():
            user = User(username="locked1", role="beobachter",
                        is_active_user=True, is_locked=True)
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()
            assert user.is_active is False

    def test_deactivated_user_is_not_active(self, app, db_session):
        with app.app_context():
            user = User(username="deact1", role="beobachter",
                        is_active_user=False, is_locked=False)
            user.set_password("x" * 8)
            db_session.session.add(user)
            db_session.session.commit()
            assert user.is_active is False
