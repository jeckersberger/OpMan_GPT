"""Authentifizierung, RBAC & Audit-Logging für OpMan-GPT.

Implementiert:
- Flask-Login Session-Management
- Rollenbasierte Zugriffskontrolle (RBAC)
- Brute-Force-Schutz (Account-Sperrung)
- Revisionssichere Audit-Protokollierung
- Login/Logout-Routen
- Admin-Benutzerverwaltung
"""
from __future__ import annotations

import functools
import hashlib
import json
from datetime import datetime, timezone, timedelta

from flask import (
    Blueprint, render_template_string, request, redirect, url_for,
    flash, jsonify, current_app, session,
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)

from models import db, User, AuditLog, UserSession, BreakGlassLog, ROLES, ROLE_HIERARCHY

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()

# ---------------------------
# Konfiguration
# ---------------------------
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15
SESSION_LIFETIME_MINUTES = 30


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------
# Flask-Login Setup
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    if user is None:
        return None
    # Session limiting: validate that the current session is still active
    sid = session.get("_opman_sid")
    if sid:
        user_session = UserSession.query.filter_by(user_id=user.id, session_id=sid).first()
        if not user_session:
            # Session was invalidated (another login occurred)
            return None
        # Update last_seen
        user_session.last_seen = _utcnow()
        db.session.commit()
    return user


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"error": "Nicht authentifiziert"}), 401
    return redirect(url_for("auth.login", next=request.url))


# ---------------------------
# Audit-Logging
# ---------------------------
def _compute_audit_hash(entry: AuditLog, previous_hash: str = None) -> str:
    """Compute SHA-256 hash for audit log entry, chained with previous entry's hash."""
    data = (
        f"{entry.timestamp.isoformat() if entry.timestamp else ''}"
        f"|{entry.user_id or ''}"
        f"|{entry.username or ''}"
        f"|{entry.action or ''}"
        f"|{entry.resource or ''}"
        f"|{entry.resource_id or ''}"
        f"|{entry.details or ''}"
        f"|{entry.ip_address or ''}"
        f"|{previous_hash or '0' * 64}"
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def audit_log(action: str, resource: str = None, resource_id: str = None,
              details: str = None, user: User = None):
    """Erstellt einen revisionssicheren Audit-Log-Eintrag mit Hash-Chain."""
    u = user or (current_user if current_user and current_user.is_authenticated else None)
    entry = AuditLog(
        timestamp=_utcnow(),
        user_id=u.id if u and hasattr(u, "id") else None,
        username=u.username if u and hasattr(u, "username") else None,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details[:2000] if details else None,
        ip_address=request.remote_addr if request else None,
        user_agent=(request.user_agent.string[:300]
                    if request and request.user_agent else None),
    )
    # Hash-chain: get the hash of the previous entry
    previous = AuditLog.query.order_by(AuditLog.id.desc()).first()
    previous_hash = previous.hash if previous and previous.hash else None
    entry.hash = _compute_audit_hash(entry, previous_hash)
    db.session.add(entry)
    # Nicht committen – wird mit dem nächsten db.session.commit() gespeichert


# ---------------------------
# RBAC Decorators
# ---------------------------
def role_required(*allowed_roles):
    """Decorator: Benutzer muss eine der angegebenen Rollen haben."""
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.has_any_role(*allowed_roles):
                audit_log("ACCESS_DENIED", resource=request.endpoint,
                          details=f"Rolle '{current_user.role}' nicht berechtigt, "
                                  f"erforderlich: {allowed_roles}")
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Keine Berechtigung"}), 403
                flash("Keine Berechtigung für diese Aktion.", "error")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def evt_or_login_required(f):
    """Decorator: Erlaubt Zugriff für eingeloggte Benutzer ODER EVT-Token."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # EVT-Token-Authentifizierung (für mobile Geräte via QR-Code)
        evt_token = (request.args.get("token")
                     or request.headers.get("X-EVT-Token")
                     or "")
        if evt_token and evt_token == current_app.config.get("EVT_ACCESS_TOKEN", ""):
            return f(*args, **kwargs)
        # Normaler Login
        if current_user and current_user.is_authenticated:
            return f(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Nicht authentifiziert"}), 401
        return redirect(url_for("auth.login", next=request.url))
    return wrapper


# ---------------------------
# Login / Logout Routen
# ---------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user and current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()

        # Brute-Force-Schutz: Account gesperrt?
        if user and user.is_locked and user.locked_until:
            if _utcnow() < user.locked_until:
                remaining = int((user.locked_until - _utcnow()).total_seconds() / 60) + 1
                audit_log("LOGIN_BLOCKED", resource="user", resource_id=username,
                          details=f"Account gesperrt, noch {remaining} Min")
                flash(f"Account gesperrt. Versuche es in {remaining} Minuten erneut.", "error")
                return _render_login()
            else:
                user.is_locked = False
                user.failed_logins = 0
                user.locked_until = None

        if user and user.check_password(password) and user.is_active:
            # Erfolgreicher Login
            user.failed_logins = 0
            user.is_locked = False
            user.locked_until = None
            user.last_login = _utcnow()
            db.session.commit()

            login_user(user, remember=False)

            # Session Limiting: invalidate all other sessions for this user
            UserSession.query.filter_by(user_id=user.id).delete()
            import secrets as _secrets
            sid = _secrets.token_urlsafe(32)
            session["_opman_sid"] = sid
            new_session = UserSession(
                user_id=user.id,
                session_id=sid,
                created_at=_utcnow(),
                last_seen=_utcnow(),
                ip_address=request.remote_addr,
                user_agent=(request.user_agent.string[:300]
                            if request.user_agent else None),
            )
            db.session.add(new_session)

            audit_log("LOGIN_SUCCESS", resource="user", resource_id=username)
            db.session.commit()

            # Anomaly detection after successful login
            check_anomalies(user, request.remote_addr)

            next_url = request.args.get("next") or request.form.get("next") or "/"
            # Sicherheit: nur relative URLs erlauben
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = "/"
            return redirect(next_url)
        else:
            # Fehlgeschlagener Login
            if user:
                user.failed_logins = (user.failed_logins or 0) + 1
                if user.failed_logins >= MAX_FAILED_LOGINS:
                    from datetime import timedelta
                    user.is_locked = True
                    user.locked_until = _utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                    audit_log("ACCOUNT_LOCKED", resource="user", resource_id=username,
                              details=f"Nach {user.failed_logins} Fehlversuchen gesperrt")
                db.session.commit()

            audit_log("LOGIN_FAILED", resource="user", resource_id=username)
            db.session.commit()
            flash("Benutzername oder Passwort falsch.", "error")

    return _render_login()


@auth_bp.route("/logout")
@login_required
def logout():
    # Remove session record
    sid = session.get("_opman_sid")
    if sid:
        UserSession.query.filter_by(session_id=sid).delete()
    audit_log("LOGOUT", resource="user", resource_id=current_user.username)
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))


# ---------------------------
# Admin: Benutzerverwaltung
# ---------------------------
@auth_bp.route("/admin/users")
@login_required
def admin_users():
    if not current_user.has_role("admin"):
        flash("Keine Berechtigung.", "error")
        return redirect("/")
    users = User.query.order_by(User.username).all()
    return _render_admin_users(users)


@auth_bp.route("/admin/users/create", methods=["POST"])
@login_required
def admin_create_user():
    if not current_user.has_role("admin"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    role = request.form.get("role") or "beobachter"
    display_name = (request.form.get("display_name") or "").strip() or None

    if not username or not password:
        flash("Benutzername und Passwort sind Pflichtfelder.", "error")
        return redirect(url_for("auth.admin_users"))

    if len(password) < 8:
        flash("Passwort muss mindestens 8 Zeichen lang sein.", "error")
        return redirect(url_for("auth.admin_users"))

    if role not in ROLES:
        flash("Ungültige Rolle.", "error")
        return redirect(url_for("auth.admin_users"))

    if User.query.filter_by(username=username).first():
        flash(f"Benutzer '{username}' existiert bereits.", "error")
        return redirect(url_for("auth.admin_users"))

    user = User(username=username, role=role, display_name=display_name)
    user.set_password(password)
    db.session.add(user)

    audit_log("USER_CREATED", resource="user", resource_id=username,
              details=f"Rolle: {role}")
    db.session.commit()

    flash(f"Benutzer '{username}' erstellt.", "success")
    return redirect(url_for("auth.admin_users"))


@auth_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    if not current_user.has_role("admin"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Sie können sich nicht selbst löschen.", "error")
        return redirect(url_for("auth.admin_users"))

    audit_log("USER_DELETED", resource="user", resource_id=user.username)
    db.session.delete(user)
    db.session.commit()

    flash(f"Benutzer '{user.username}' gelöscht.", "success")
    return redirect(url_for("auth.admin_users"))


@auth_bp.route("/admin/users/<int:user_id>/toggle-lock", methods=["POST"])
@login_required
def admin_toggle_lock(user_id):
    if not current_user.has_role("admin"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Sie können sich nicht selbst sperren.", "error")
        return redirect(url_for("auth.admin_users"))

    user.is_locked = not user.is_locked
    if not user.is_locked:
        user.failed_logins = 0
        user.locked_until = None

    action = "USER_LOCKED" if user.is_locked else "USER_UNLOCKED"
    audit_log(action, resource="user", resource_id=user.username)
    db.session.commit()

    status = "gesperrt" if user.is_locked else "entsperrt"
    flash(f"Benutzer '{user.username}' {status}.", "success")
    return redirect(url_for("auth.admin_users"))


@auth_bp.route("/admin/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
def admin_reset_password(user_id):
    if not current_user.has_role("admin"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    user = db.get_or_404(User, user_id)
    new_password = request.form.get("new_password") or ""

    if len(new_password) < 8:
        flash("Passwort muss mindestens 8 Zeichen lang sein.", "error")
        return redirect(url_for("auth.admin_users"))

    user.set_password(new_password)
    user.failed_logins = 0
    user.is_locked = False
    user.locked_until = None

    audit_log("PASSWORD_RESET", resource="user", resource_id=user.username,
              details=f"Durch Admin: {current_user.username}")
    db.session.commit()

    flash(f"Passwort für '{user.username}' zurückgesetzt.", "success")
    return redirect(url_for("auth.admin_users"))


# ---------------------------
# Audit-Log Ansicht
# ---------------------------
@auth_bp.route("/admin/audit-log")
@login_required
def admin_audit_log():
    if not current_user.has_any_role("admin", "schichtleiter", "datenschutz"):
        flash("Keine Berechtigung.", "error")
        return redirect("/")

    page = request.args.get("page", 1, type=int)
    per_page = 50
    logs = (AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all())
    total = AuditLog.query.count()
    return _render_audit_log(logs, page, per_page, total)


# ---------------------------
# API: Audit-Log Export
# ---------------------------
@auth_bp.route("/api/audit-log")
@login_required
def api_audit_log():
    if not current_user.has_any_role("admin", "schichtleiter", "datenschutz"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    limit = min(request.args.get("limit", 100, type=int), 1000)
    offset = request.args.get("offset", 0, type=int)
    logs = (AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .limit(limit).offset(offset).all())
    return jsonify([{
        "id": l.id,
        "timestamp": l.timestamp.isoformat() + "Z" if l.timestamp else None,
        "user_id": l.user_id,
        "username": l.username,
        "action": l.action,
        "resource": l.resource,
        "resource_id": l.resource_id,
        "details": l.details,
        "ip_address": l.ip_address,
    } for l in logs])


# ---------------------------
# Init-Funktion
# ---------------------------
def init_auth(app):
    """Initialisiert Flask-Login, registriert Blueprint (vor db.create_all aufrufen)."""
    from datetime import timedelta
    import secrets

    # EVT-Access-Token generieren (für QR-Codes)
    if not app.config.get("EVT_ACCESS_TOKEN"):
        import os
        token_file = os.path.join(os.path.dirname(__file__), "instance", "evt_token.txt")
        if os.path.exists(token_file):
            with open(token_file) as f:
                app.config["EVT_ACCESS_TOKEN"] = f.read().strip()
        else:
            token = secrets.token_urlsafe(32)
            app.config["EVT_ACCESS_TOKEN"] = token
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, "w") as f:
                f.write(token)

    # Flask-Login konfigurieren
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Bitte melden Sie sich an."
    login_manager.login_message_category = "info"

    # Session-Konfiguration (sichere Cookies)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=SESSION_LIFETIME_MINUTES)
    # SESSION_COOKIE_SECURE nur wenn nicht localhost
    if app.config.get("SECRET_KEY", "") != "dev-only-change-in-production":
        app.config["SESSION_COOKIE_SECURE"] = True

    # Blueprint registrieren
    app.register_blueprint(auth_bp)

    # Register after_request handler for API audit logging
    _register_after_request(app)


def create_default_admin():
    """Erstellt den Standard-Admin falls noch keiner existiert (nach db.create_all aufrufen)."""
    if User.query.count() == 0:
        admin = User(
            username="admin",
            role="admin",
            display_name="System-Administrator",
        )
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()
        print("[auth] Standard-Admin erstellt: admin / admin")
        print("[auth] WICHTIG: Passwort nach dem ersten Login aendern!")


# ---------------------------
# Anomaly Detection (basic)
# ---------------------------
# Configurable business hours (24h format)
BUSINESS_HOURS_START = 6   # 06:00
BUSINESS_HOURS_END = 22    # 22:00
ANOMALY_FAILED_LOGIN_THRESHOLD = 5
ANOMALY_FAILED_LOGIN_WINDOW_MINUTES = 10


def check_anomalies(user: User, ip_address: str):
    """Run basic anomaly detection checks after a successful login.

    Checks:
    - Multiple failed logins from same IP in short time window
    - Login from a new IP for this user (compared to last 10 logins)
    - Access outside configurable business hours
    Logs anomalies as ANOMALY_DETECTED audit entries.
    """
    now = _utcnow()

    # 1. Multiple failed logins from same IP in short time window
    window_start = now - timedelta(minutes=ANOMALY_FAILED_LOGIN_WINDOW_MINUTES)
    failed_from_ip = AuditLog.query.filter(
        AuditLog.action == "LOGIN_FAILED",
        AuditLog.ip_address == ip_address,
        AuditLog.timestamp >= window_start,
    ).count()
    if failed_from_ip >= ANOMALY_FAILED_LOGIN_THRESHOLD:
        audit_log(
            "ANOMALY_DETECTED",
            resource="login",
            resource_id=user.username,
            details=f"Multiple failed logins ({failed_from_ip}) from IP {ip_address} "
                    f"in last {ANOMALY_FAILED_LOGIN_WINDOW_MINUTES} minutes",
            user=user,
        )

    # 2. Login from new IP for this user (compared to last 10 successful logins)
    recent_logins = (
        AuditLog.query
        .filter(
            AuditLog.action == "LOGIN_SUCCESS",
            AuditLog.username == user.username,
            AuditLog.ip_address.isnot(None),
        )
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )
    known_ips = {log.ip_address for log in recent_logins}
    if known_ips and ip_address not in known_ips:
        audit_log(
            "ANOMALY_DETECTED",
            resource="login",
            resource_id=user.username,
            details=f"Login from new IP {ip_address}. "
                    f"Known IPs: {', '.join(sorted(known_ips))}",
            user=user,
        )

    # 3. Access outside business hours
    if now.hour < BUSINESS_HOURS_START or now.hour >= BUSINESS_HOURS_END:
        audit_log(
            "ANOMALY_DETECTED",
            resource="login",
            resource_id=user.username,
            details=f"Login outside business hours at {now.strftime('%H:%M')} UTC "
                    f"(business hours: {BUSINESS_HOURS_START:02d}:00-{BUSINESS_HOURS_END:02d}:00)",
            user=user,
        )

    db.session.commit()


# ---------------------------
# Break-Glass Emergency Access
# ---------------------------
@auth_bp.route("/admin/break-glass", methods=["POST"])
@login_required
def admin_break_glass():
    """Emergency access elevation - requires reason, auto-expires after 1 hour."""
    reason = (request.form.get("reason") or request.json.get("reason", "") if request.is_json else request.form.get("reason") or "").strip()

    if not reason:
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Reason is required for break-glass access"}), 400
        flash("Ein Grund ist erforderlich fuer den Notfallzugriff.", "error")
        return redirect(url_for("auth.admin_users"))

    now = _utcnow()
    expires_at = now + timedelta(hours=1)

    bg_entry = BreakGlassLog(
        user_id=current_user.id,
        timestamp=now,
        reason=reason,
        approved_by=current_user.username,
        expires_at=expires_at,
    )
    db.session.add(bg_entry)

    # Prominent audit logging with warnings
    audit_log(
        "BREAK_GLASS_ACTIVATED",
        resource="emergency_access",
        resource_id=str(current_user.id),
        details=f"WARNING: Break-glass emergency access activated by {current_user.username}. "
                f"Reason: {reason}. Expires at: {expires_at.isoformat()}Z. "
                f"THIS EVENT REQUIRES REVIEW.",
        user=current_user,
    )
    db.session.commit()

    print(f"[BREAK-GLASS WARNING] User '{current_user.username}' activated emergency access. "
          f"Reason: {reason}. Expires: {expires_at.isoformat()}Z")

    if request.is_json:
        return jsonify({
            "status": "break-glass activated",
            "user": current_user.username,
            "reason": reason,
            "expires_at": expires_at.isoformat() + "Z",
            "warning": "This event has been audit-logged and requires review.",
        }), 200

    flash(f"Notfallzugriff aktiviert. Laeuft ab: {expires_at.strftime('%H:%M:%S')} UTC. "
          f"Dieses Ereignis wurde protokolliert.", "success")
    return redirect(url_for("auth.admin_users"))


# ---------------------------
# Data Retention
# ---------------------------
@auth_bp.route("/api/admin/data-retention", methods=["POST"])
@login_required
def api_data_retention():
    """Delete audit logs older than configurable retention period (default 365 days).
    Only accessible by admin role.
    """
    if not current_user.has_role("admin"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    retention_days = request.json.get("retention_days", 365) if request.is_json else 365
    try:
        retention_days = int(retention_days)
    except (ValueError, TypeError):
        return jsonify({"error": "retention_days must be an integer"}), 400

    if retention_days < 1:
        return jsonify({"error": "retention_days must be at least 1"}), 400

    cutoff = _utcnow() - timedelta(days=retention_days)
    count = AuditLog.query.filter(AuditLog.timestamp < cutoff).count()
    AuditLog.query.filter(AuditLog.timestamp < cutoff).delete()

    audit_log(
        "DATA_RETENTION_EXECUTED",
        resource="audit_log",
        details=f"Deleted {count} audit log entries older than {retention_days} days "
                f"(cutoff: {cutoff.isoformat()}Z)",
    )
    db.session.commit()

    return jsonify({
        "status": "ok",
        "deleted_count": count,
        "retention_days": retention_days,
        "cutoff_date": cutoff.isoformat() + "Z",
    })


# ---------------------------
# Access Review
# ---------------------------
@auth_bp.route("/api/admin/access-review", methods=["GET"])
@login_required
def api_access_review():
    """Returns a report of all users, their roles, last login,
    and whether review is overdue (>90 days since last review).
    Only accessible by admin role.
    """
    if not current_user.has_role("admin"):
        return jsonify({"error": "Keine Berechtigung"}), 403

    now = _utcnow()
    review_threshold = timedelta(days=90)
    users = User.query.order_by(User.username).all()

    report = []
    for u in users:
        overdue = False
        if u.last_review_at is None:
            overdue = True
        elif (now - u.last_review_at) > review_threshold:
            overdue = True

        report.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "display_name": u.display_name,
            "is_active": u.is_active,
            "is_locked": u.is_locked,
            "last_login": (u.last_login.isoformat() + "Z") if u.last_login else None,
            "last_review_at": (u.last_review_at.isoformat() + "Z") if u.last_review_at else None,
            "review_overdue": overdue,
        })

    audit_log("ACCESS_REVIEW_GENERATED", resource="users",
              details=f"Report generated with {len(report)} users")
    db.session.commit()

    return jsonify({
        "generated_at": now.isoformat() + "Z",
        "total_users": len(report),
        "overdue_count": sum(1 for r in report if r["review_overdue"]),
        "users": report,
    })


# ---------------------------
# Enhanced Audit: @after_request for /api/ paths
# ---------------------------
def _register_after_request(app):
    """Register an after_request handler that logs ALL API access for /api/ paths."""
    @app.after_request
    def log_api_access(response):
        if request.path.startswith("/api/"):
            try:
                u = current_user if current_user and current_user.is_authenticated else None
                entry = AuditLog(
                    timestamp=_utcnow(),
                    user_id=u.id if u and hasattr(u, "id") else None,
                    username=u.username if u and hasattr(u, "username") else None,
                    action="API_ACCESS",
                    resource=request.path,
                    resource_id=request.method,
                    details=f"{request.method} {request.path} -> {response.status_code}",
                    ip_address=request.remote_addr,
                    user_agent=(request.user_agent.string[:300]
                                if request.user_agent else None),
                )
                # Hash-chain
                previous = AuditLog.query.order_by(AuditLog.id.desc()).first()
                previous_hash = previous.hash if previous and previous.hash else None
                entry.hash = _compute_audit_hash(entry, previous_hash)
                db.session.add(entry)
                db.session.commit()
            except Exception:
                # Never let audit logging break the response
                pass
        return response


# ═══════════════════════════════════════════════════════════════
# Templates (inline, um keine zusätzlichen Dateien zu benötigen)
# ═══════════════════════════════════════════════════════════════

_BASE_STYLE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0d1117; color: #e6edf3; line-height: 1.6;
  }
  .container { max-width: 480px; margin: 0 auto; padding: 2rem 1rem; }
  .container-wide { max-width: 960px; margin: 0 auto; padding: 1rem; }
  h1, h2 { margin-bottom: 1rem; }
  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 1.5rem; margin-bottom: 1rem;
  }
  label { display: block; margin-bottom: .25rem; font-weight: 600; font-size: .9rem; }
  input[type="text"], input[type="password"], select {
    width: 100%; padding: .6rem .8rem; border: 1px solid #30363d;
    border-radius: 6px; background: #0d1117; color: #e6edf3;
    font-size: 1rem; margin-bottom: .75rem;
  }
  input:focus, select:focus { outline: none; border-color: #58a6ff; }
  .btn {
    display: inline-block; padding: .6rem 1.2rem; border: none; border-radius: 6px;
    font-size: .95rem; font-weight: 600; cursor: pointer; text-decoration: none;
    text-align: center;
  }
  .btn-primary { background: #2563eb; color: #fff; }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-danger { background: #dc2626; color: #fff; }
  .btn-danger:hover { background: #b91c1c; }
  .btn-sm { padding: .35rem .7rem; font-size: .8rem; }
  .btn-block { display: block; width: 100%; }
  .flash { padding: .6rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: .9rem; }
  .flash-error { background: #3d1a1a; border: 1px solid #dc2626; color: #fca5a5; }
  .flash-success { background: #1a3d1a; border: 1px solid #22c55e; color: #86efac; }
  .flash-info { background: #1a2a3d; border: 1px solid #3b82f6; color: #93c5fd; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: .5rem .7rem; text-align: left; border-bottom: 1px solid #21262d; font-size: .85rem; }
  th { background: #161b22; font-weight: 600; }
  .badge {
    display: inline-block; padding: .15rem .5rem; border-radius: 10px;
    font-size: .75rem; font-weight: 600;
  }
  .badge-green { background: #22c55e20; color: #22c55e; }
  .badge-red { background: #dc262620; color: #dc2626; }
  .badge-blue { background: #3b82f620; color: #3b82f6; }
  a { color: #58a6ff; }
  .topbar-auth {
    background: #161b22; border-bottom: 1px solid #30363d;
    padding: .5rem 1rem; display: flex; justify-content: space-between; align-items: center;
    font-size: .85rem;
  }
  .topbar-auth a { margin-left: 1rem; }
  .text-muted { color: #8b949e; }
  .mt-1 { margin-top: .5rem; }
  .mb-1 { margin-bottom: .5rem; }
  .flex-gap { display: flex; gap: .5rem; align-items: center; }
</style>
"""

_FLASH_BLOCK = """
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    {% for category, message in messages %}
      <div class="flash flash-{{ category }}">{{ message }}</div>
    {% endfor %}
  {% endif %}
{% endwith %}
"""


def _render_login():
    return render_template_string("""
<!doctype html>
<html lang="de"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login – OpMan-GPT</title>
""" + _BASE_STYLE + """
</head><body>
<div class="container">
  <div style="text-align:center;margin-bottom:2rem;">
    <h1 style="font-size:1.5rem;">OpMan-GPT</h1>
    <p class="text-muted">Einsatzleitstand – Anmeldung</p>
  </div>

  """ + _FLASH_BLOCK + """

  <div class="card">
    <form method="POST" action="{{ url_for('auth.login', next=request.args.get('next','')) }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <label for="username">Benutzername</label>
      <input type="text" id="username" name="username" required autofocus
             autocomplete="username" autocapitalize="none">

      <label for="password">Passwort</label>
      <input type="password" id="password" name="password" required
             autocomplete="current-password">

      <button type="submit" class="btn btn-primary btn-block" style="margin-top:.5rem;">
        Anmelden
      </button>
    </form>
  </div>

  <p class="text-muted" style="text-align:center;font-size:.8rem;">
    Standardzugang: admin / admin
  </p>
</div>
</body></html>
""")


def _render_admin_users(users):
    return render_template_string("""
<!doctype html>
<html lang="de"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Benutzerverwaltung – OpMan-GPT</title>
""" + _BASE_STYLE + """
</head><body>
<div class="topbar-auth">
  <span>Angemeldet: <b>{{ current_user.username }}</b> ({{ current_user.role }})</span>
  <div>
    <a href="/">Einsatzleiter</a>
    <a href="{{ url_for('auth.admin_audit_log') }}">Audit-Log</a>
    <a href="{{ url_for('auth.logout') }}">Abmelden</a>
  </div>
</div>
<div class="container-wide">
  <h2>Benutzerverwaltung</h2>

  """ + _FLASH_BLOCK + """

  <div class="card">
    <h3 style="margin-bottom:.75rem;">Neuen Benutzer anlegen</h3>
    <form method="POST" action="{{ url_for('auth.admin_create_user') }}"
          style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:.5rem;align-items:end;">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div>
        <label>Benutzername</label>
        <input type="text" name="username" required style="margin:0">
      </div>
      <div>
        <label>Passwort (min. 8)</label>
        <input type="password" name="password" required minlength="8" style="margin:0">
      </div>
      <div>
        <label>Rolle</label>
        <select name="role" style="margin:0">
          {% for key, desc in roles.items() %}
          <option value="{{ key }}">{{ key }}</option>
          {% endfor %}
        </select>
      </div>
      <button type="submit" class="btn btn-primary btn-sm">Erstellen</button>
    </form>
  </div>

  <table>
    <thead>
      <tr>
        <th>Benutzer</th><th>Rolle</th><th>Status</th>
        <th>Fehlversuche</th><th>Letzter Login</th><th>Aktionen</th>
      </tr>
    </thead>
    <tbody>
      {% for user in users %}
      <tr>
        <td><b>{{ user.username }}</b>
            {% if user.display_name %}<br><span class="text-muted">{{ user.display_name }}</span>{% endif %}
        </td>
        <td><span class="badge badge-blue">{{ user.role }}</span></td>
        <td>
          {% if user.is_locked %}
            <span class="badge badge-red">Gesperrt</span>
          {% elif user.is_active %}
            <span class="badge badge-green">Aktiv</span>
          {% else %}
            <span class="badge badge-red">Deaktiviert</span>
          {% endif %}
        </td>
        <td>{{ user.failed_logins }}</td>
        <td class="text-muted">{{ user.last_login.strftime('%d.%m.%Y %H:%M') if user.last_login else '–' }}</td>
        <td>
          <div class="flex-gap">
            {% if user.id != current_user.id %}
            <form method="POST" action="{{ url_for('auth.admin_toggle_lock', user_id=user.id) }}" style="margin:0">
              <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
              <button class="btn btn-sm {% if user.is_locked %}btn-primary{% else %}btn-danger{% endif %}">
                {{ 'Entsperren' if user.is_locked else 'Sperren' }}
              </button>
            </form>
            <form method="POST" action="{{ url_for('auth.admin_delete_user', user_id=user.id) }}"
                  style="margin:0" onsubmit="return confirm('Benutzer wirklich löschen?')">
              <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
              <button class="btn btn-danger btn-sm">Löschen</button>
            </form>
            {% endif %}
          </div>
          <form method="POST" action="{{ url_for('auth.admin_reset_password', user_id=user.id) }}"
                style="margin-top:.3rem;display:flex;gap:.3rem;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <input type="password" name="new_password" placeholder="Neues Passwort" minlength="8"
                   style="margin:0;padding:.25rem .5rem;font-size:.8rem;flex:1">
            <button class="btn btn-sm btn-primary">PW Reset</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div style="margin-top:1.5rem;" class="card">
    <h3>EVT-Zugangstoken</h3>
    <p class="text-muted" style="font-size:.85rem;margin-bottom:.5rem;">
      Dieses Token wird in QR-Codes eingebettet, damit EVT-Geräte ohne Login Zugriff haben.
    </p>
    <code style="background:#0d1117;padding:.4rem .8rem;border-radius:4px;font-size:.8rem;word-break:break-all;">
      {{ config.get('EVT_ACCESS_TOKEN', '–') }}
    </code>
  </div>
</div>
</body></html>
""", users=users, roles=ROLES, config=current_app.config)


def _render_audit_log(logs, page, per_page, total):
    return render_template_string("""
<!doctype html>
<html lang="de"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit-Log – OpMan-GPT</title>
""" + _BASE_STYLE + """
</head><body>
<div class="topbar-auth">
  <span>Angemeldet: <b>{{ current_user.username }}</b> ({{ current_user.role }})</span>
  <div>
    <a href="/">Einsatzleiter</a>
    <a href="{{ url_for('auth.admin_users') }}">Benutzer</a>
    <a href="{{ url_for('auth.logout') }}">Abmelden</a>
  </div>
</div>
<div class="container-wide">
  <h2>Audit-Log</h2>
  <p class="text-muted mb-1">{{ total }} Einträge gesamt – Seite {{ page }}</p>

  <table>
    <thead>
      <tr>
        <th>Zeitpunkt</th><th>Benutzer</th><th>Aktion</th>
        <th>Ressource</th><th>Details</th><th>IP</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs %}
      <tr>
        <td class="text-muted" style="white-space:nowrap">
          {{ log.timestamp.strftime('%d.%m.%Y %H:%M:%S') if log.timestamp else '–' }}
        </td>
        <td>{{ log.username or '–' }}</td>
        <td>
          <span class="badge {% if 'FAIL' in log.action or 'DENIED' in log.action or 'LOCKED' in log.action %}badge-red{% elif 'SUCCESS' in log.action or 'CREATED' in log.action %}badge-green{% else %}badge-blue{% endif %}">
            {{ log.action }}
          </span>
        </td>
        <td>{{ log.resource or '' }} {{ log.resource_id or '' }}</td>
        <td class="text-muted" style="max-width:300px;overflow:hidden;text-overflow:ellipsis;">
          {{ log.details or '' }}
        </td>
        <td class="text-muted">{{ log.ip_address or '' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div style="margin-top:1rem;display:flex;gap:1rem;justify-content:center;">
    {% if page > 1 %}
    <a href="?page={{ page - 1 }}" class="btn btn-sm btn-primary">Vorherige</a>
    {% endif %}
    {% if page * per_page < total %}
    <a href="?page={{ page + 1 }}" class="btn btn-sm btn-primary">Nächste</a>
    {% endif %}
  </div>
</div>
</body></html>
""", logs=logs, page=page, per_page=per_page, total=total)
