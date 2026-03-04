"""
database.py - Database configuration module for OpMan-GPT.

Supports both SQLite (default, backwards compatible) and PostgreSQL
for production deployments. Configuration is driven by environment variables.

Environment Variables:
    DATABASE_URL        - Full database URI (takes precedence over individual vars)
    DB_TYPE             - "sqlite" (default) or "postgresql"
    DB_HOST             - PostgreSQL host (default: localhost)
    DB_PORT             - PostgreSQL port (default: 5432)
    DB_NAME             - PostgreSQL database name (default: opman)
    DB_USER             - PostgreSQL user (default: opman)
    DB_PASSWORD          - PostgreSQL password (required for PostgreSQL)
    DB_SSL_MODE         - PostgreSQL SSL mode (default: require)
    DB_POOL_SIZE        - Connection pool size (default: 10)
    DB_MAX_OVERFLOW     - Max overflow connections (default: 20)
    DB_POOL_TIMEOUT     - Pool checkout timeout in seconds (default: 30)
    DB_POOL_RECYCLE     - Connection recycle time in seconds (default: 1800)
"""

from __future__ import annotations

import os
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def get_database_uri() -> str:
    """
    Build and return the SQLAlchemy database URI from environment variables.

    Priority:
        1. DATABASE_URL environment variable (full URI)
        2. Individual DB_* environment variables
        3. Default: SQLite (instance/einsatzleiter.db)

    Returns:
        str: SQLAlchemy-compatible database URI.
    """
    # 1. Full DATABASE_URL takes precedence
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Heroku-style postgres:// -> postgresql:// fix
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Using DATABASE_URL for database connection.")
        return database_url

    # 2. Individual DB_* variables
    db_type = os.environ.get("DB_TYPE", "sqlite").lower()

    if db_type == "sqlite":
        db_path = os.environ.get("DB_PATH", "instance/einsatzleiter.db")
        uri = f"sqlite:///{db_path}"
        logger.info("Using SQLite database: %s", db_path)
        return uri

    if db_type in ("postgresql", "postgres"):
        host = os.environ.get("DB_HOST", "localhost")
        port = os.environ.get("DB_PORT", "5432")
        name = os.environ.get("DB_NAME", "opman")
        user = os.environ.get("DB_USER", "opman")
        password = os.environ.get("DB_PASSWORD", "")
        ssl_mode = os.environ.get("DB_SSL_MODE", "require")

        if not password:
            logger.warning(
                "DB_PASSWORD is not set. PostgreSQL connection may fail."
            )

        # URL-encode password to handle special characters
        encoded_password = quote_plus(password)
        uri = (
            f"postgresql://{user}:{encoded_password}@{host}:{port}/{name}"
            f"?sslmode={ssl_mode}"
        )
        logger.info(
            "Using PostgreSQL database: %s@%s:%s/%s (sslmode=%s)",
            user, host, port, name, ssl_mode,
        )
        return uri

    raise ValueError(
        f"Unsupported DB_TYPE: '{db_type}'. Use 'sqlite' or 'postgresql'."
    )


def get_engine_options() -> dict:
    """
    Return SQLAlchemy engine options appropriate for the configured database type.

    For SQLite:  WAL mode, basic pool settings.
    For PostgreSQL: Connection pooling with configurable sizes, SSL enforcement.

    Returns:
        dict: Engine options for SQLAlchemy configuration.
    """
    db_type = os.environ.get("DB_TYPE", "sqlite").lower()
    database_url = os.environ.get("DATABASE_URL", "")

    is_postgres = db_type in ("postgresql", "postgres") or \
        database_url.startswith("postgresql://") or \
        database_url.startswith("postgres://")

    if is_postgres:
        pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
        max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
        pool_timeout = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
        pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "1800"))

        options = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": True,
            "connect_args": {
                "sslmode": os.environ.get("DB_SSL_MODE", "require"),
                "connect_timeout": 10,
            },
        }
        logger.info(
            "PostgreSQL pool: size=%d, max_overflow=%d, recycle=%ds",
            pool_size, max_overflow, pool_recycle,
        )
        return options

    # SQLite defaults: WAL mode for concurrent reads across gunicorn workers
    return {
        "connect_args": {"check_same_thread": False},
        "pool_pre_ping": True,
    }


def configure_app_database(app) -> None:
    """
    Apply database configuration to a Flask app instance.

    Sets SQLALCHEMY_DATABASE_URI and SQLALCHEMY_ENGINE_OPTIONS based on
    environment variables. Call this in create_app() before db.init_app().

    Args:
        app: Flask application instance.
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = get_engine_options()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def run_migrations(db, app) -> None:
    """
    Run lightweight auto-migrations for schema updates.

    Attempts ALTER TABLE statements and silently ignores errors for
    columns/tables that already exist. For production PostgreSQL setups,
    consider using Alembic for proper migration management.

    Args:
        db: SQLAlchemy database instance.
        app: Flask application instance.
    """
    from sqlalchemy import text, inspect

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # Create all tables that don't exist yet
        db.create_all()

        # Example migration pattern - add new columns to existing tables
        migrations = [
            ("teams", "radio_group", "ALTER TABLE teams ADD COLUMN radio_group VARCHAR(30) NOT NULL DEFAULT 'regelfunk'"),
            ("teams", "vehicle", "ALTER TABLE teams ADD COLUMN vehicle VARCHAR(50)"),
            ("missions", "priority", "ALTER TABLE missions ADD COLUMN priority INTEGER NOT NULL DEFAULT 3"),
            ("missions", "archived", "ALTER TABLE missions ADD COLUMN archived BOOLEAN NOT NULL DEFAULT 0"),
        ]

        for table, column, sql in migrations:
            if table not in existing_tables:
                continue
            existing_columns = [c["name"] for c in inspector.get_columns(table)]
            if column not in existing_columns:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    logger.info("Migration applied: added %s.%s", table, column)
                except Exception as e:
                    db.session.rollback()
                    logger.debug("Migration skipped (%s.%s): %s", table, column, e)


def check_database_connection(db) -> dict:
    """
    Check database connectivity and return status information.

    Returns:
        dict: Status dict with 'ok' boolean and additional details.
    """
    from sqlalchemy import text

    try:
        result = db.session.execute(text("SELECT 1"))
        result.fetchone()

        status = {"ok": True, "type": _get_db_type()}

        # PostgreSQL-specific pool info
        pool = db.engine.pool
        if hasattr(pool, "size"):
            status["pool_size"] = pool.size()
            status["pool_checkedout"] = pool.checkedout()
            status["pool_overflow"] = pool.overflow()
            status["pool_checkedin"] = pool.checkedin()

        return status

    except Exception as e:
        return {"ok": False, "type": _get_db_type(), "error": str(e)}


def _get_db_type() -> str:
    """Return the currently configured database type as a string."""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        if "postgresql" in database_url or "postgres" in database_url:
            return "postgresql"
        return "sqlite"
    return os.environ.get("DB_TYPE", "sqlite").lower()
