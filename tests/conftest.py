"""Shared pytest fixtures for OpMan-GPT test suite."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing.

    Disables Flask-Limiter to prevent 429 errors during tests by
    patching the Limiter class to start with enabled=False.
    """
    # Patch Limiter to disable rate limiting during testing
    import flask_limiter
    _OriginalLimiter = flask_limiter.Limiter

    class _DisabledLimiter(_OriginalLimiter):
        def __init__(self, *args, **kwargs):
            kwargs["enabled"] = False
            super().__init__(*args, **kwargs)

    with patch.object(flask_limiter, "Limiter", _DisabledLimiter):
        # Also patch the import location used by app.py
        with patch("flask_limiter.Limiter", _DisabledLimiter):
            from app import create_app
            application = create_app()

    # Override config for testing
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret-key-not-for-production",
        EVT_ACCESS_TOKEN="test-evt-token-12345",
        SERVER_NAME="localhost",
        RATELIMIT_ENABLED=False,
    )

    yield application


# ---------------------------------------------------------------------------
# Database session fixture -- clean state BEFORE each test
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def db_session(app):
    """Provide a clean database session for every test.

    Truncates all tables BEFORE the test runs so each test starts fresh.
    """
    from models import db

    with app.app_context():
        # Clean all tables before the test
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        yield db
        # After test: just rollback any uncommitted changes
        db.session.rollback()


# ---------------------------------------------------------------------------
# Test client
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def admin_user(app, db_session):
    """Create and return an admin user."""
    from models import User
    with app.app_context():
        user = User(username="testadmin", role="admin", display_name="Test Admin")
        user.set_password("Admin1234!")
        db_session.session.add(user)
        db_session.session.commit()
        return User.query.filter_by(username="testadmin").first()


@pytest.fixture()
def disponent_user(app, db_session):
    """Create and return a disponent user."""
    from models import User
    with app.app_context():
        user = User(username="testdisponent", role="disponent", display_name="Test Disponent")
        user.set_password("Dispo1234!")
        db_session.session.add(user)
        db_session.session.commit()
        return User.query.filter_by(username="testdisponent").first()


@pytest.fixture()
def beobachter_user(app, db_session):
    """Create and return a beobachter (observer) user."""
    from models import User
    with app.app_context():
        user = User(username="testbeobachter", role="beobachter", display_name="Test Beobachter")
        user.set_password("Beob1234!")
        db_session.session.add(user)
        db_session.session.commit()
        return User.query.filter_by(username="testbeobachter").first()


# ---------------------------------------------------------------------------
# Authenticated client helpers
# ---------------------------------------------------------------------------
def _login(client, username, password):
    """Helper to log in via the login form."""
    return client.post("/login", data={
        "username": username,
        "password": password,
    }, follow_redirects=True)


@pytest.fixture()
def auth_client(app, client, admin_user):
    """A test client that is already authenticated as admin."""
    with app.app_context():
        _login(client, "testadmin", "Admin1234!")
    return client


@pytest.fixture()
def disponent_client(app, client, disponent_user):
    """A test client authenticated as disponent."""
    with app.app_context():
        _login(client, "testdisponent", "Dispo1234!")
    return client


@pytest.fixture()
def beobachter_client(app, client, beobachter_user):
    """A test client authenticated as beobachter."""
    with app.app_context():
        _login(client, "testbeobachter", "Beob1234!")
    return client
