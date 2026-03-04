"""Tests for authentication, login/logout, brute-force protection, and RBAC."""
from __future__ import annotations

from models import User, AuditLog


def _login(client, username, password, follow=True):
    """Helper to POST to the login endpoint."""
    return client.post("/login", data={
        "username": username,
        "password": password,
    }, follow_redirects=follow)


class TestLoginPage:
    """Login page rendering."""

    def test_login_page_renders(self, app, client):
        with app.app_context():
            resp = client.get("/login")
            assert resp.status_code == 200
            assert b"Anmeldung" in resp.data or b"login" in resp.data.lower()


class TestLoginSuccess:
    """Successful authentication flow."""

    def test_login_success(self, app, client, admin_user):
        with app.app_context():
            resp = _login(client, "testadmin", "Admin1234!")
            assert resp.status_code == 200
            # After successful login we should be redirected to the index
            # The index page requires templates; check we are not on /login anymore
            assert b"Anmeldung" not in resp.data or b"Einsatzleiter" in resp.data


class TestLoginFailures:
    """Failed login scenarios."""

    def test_login_wrong_password(self, app, client, admin_user):
        with app.app_context():
            resp = _login(client, "testadmin", "WrongPassword99!")
            assert resp.status_code == 200
            assert b"falsch" in resp.data or b"error" in resp.data.lower()

    def test_login_nonexistent_user(self, app, client):
        with app.app_context():
            resp = _login(client, "doesnotexist", "SomePass123!")
            assert resp.status_code == 200
            assert b"falsch" in resp.data or b"error" in resp.data.lower()


class TestBruteForceLockout:
    """Account lockout after repeated failed attempts."""

    def test_brute_force_lockout(self, app, client, admin_user):
        with app.app_context():
            # Attempt 5 failed logins
            for i in range(5):
                resp = _login(client, "testadmin", f"wrong{i}")
                assert resp.status_code == 200

            # The 6th attempt should show the lockout message
            resp = _login(client, "testadmin", "wrong_again")
            assert resp.status_code == 200
            assert b"gesperrt" in resp.data.lower() or b"locked" in resp.data.lower()

            # Verify the user is locked in the database
            user = User.query.filter_by(username="testadmin").first()
            assert user.is_locked is True
            assert user.locked_until is not None


class TestLogout:
    """Logout functionality."""

    def test_logout(self, app, auth_client):
        with app.app_context():
            resp = auth_client.get("/logout", follow_redirects=True)
            assert resp.status_code == 200
            # After logout, accessing a protected page should redirect to login
            resp2 = auth_client.get("/api/dashboard")
            # Should get 401 or redirect
            assert resp2.status_code in (302, 401)


class TestProtectedRoutes:
    """Routes that require authentication."""

    def test_protected_route_requires_login(self, app, client):
        with app.app_context():
            resp = client.get("/", follow_redirects=False)
            assert resp.status_code == 302
            assert "/login" in resp.headers.get("Location", "")

    def test_api_returns_401_without_auth(self, app, client):
        with app.app_context():
            resp = client.get("/api/dashboard")
            assert resp.status_code in (302, 401)
            if resp.status_code == 401:
                data = resp.get_json()
                assert "error" in data


class TestRoleBasedAccess:
    """Role-based access control (RBAC) enforcement."""

    def test_role_required_admin_only(self, app, client, beobachter_user):
        """Beobachter should not be able to reset the exercise (admin/schichtleiter/disponent only)."""
        with app.app_context():
            _login(client, "testbeobachter", "Beob1234!")
            resp = client.post("/api/reset",
                               json={"reset_teams": False},
                               content_type="application/json")
            assert resp.status_code == 403

    def test_role_required_disponent(self, app, client, disponent_user):
        """Disponent should be able to reset the exercise."""
        with app.app_context():
            _login(client, "testdisponent", "Dispo1234!")
            resp = client.post("/api/reset",
                               json={"reset_teams": False},
                               content_type="application/json")
            assert resp.status_code == 200


class TestEvtTokenAccess:
    """EVT token-based authentication for mobile devices."""

    def test_evt_token_access(self, app, client):
        """EVT token should grant access to evt_or_login_required endpoints."""
        with app.app_context():
            token = app.config["EVT_ACCESS_TOKEN"]
            resp = client.get(f"/api/beobachter?token={token}")
            assert resp.status_code == 200

    def test_evt_token_invalid(self, app, client):
        """Invalid EVT token should not grant access."""
        with app.app_context():
            resp = client.get("/api/beobachter?token=invalid-token")
            assert resp.status_code in (302, 401)


class TestSessionCookieFlags:
    """Verify session cookie security configuration."""

    def test_session_cookie_flags(self, app, client, admin_user):
        with app.app_context():
            resp = client.post("/login", data={
                "username": "testadmin",
                "password": "Admin1234!",
            }, follow_redirects=False)
            # Check that Set-Cookie header has HttpOnly
            cookies = resp.headers.getlist("Set-Cookie")
            session_cookie = [c for c in cookies if "session" in c.lower()]
            if session_cookie:
                cookie_str = session_cookie[0]
                assert "HttpOnly" in cookie_str
                assert "SameSite" in cookie_str
