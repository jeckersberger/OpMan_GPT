from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()


# ---------------------------
# Rollen-Definitionen (RBAC)
# ---------------------------
ROLES = {
    "admin":              "Administrator – Systemkonfiguration, Benutzerverwaltung",
    "disponent":          "Disponent – Einsatzverwaltung, Alarmierung, Disposition",
    "schichtleiter":      "Schichtleiter – Erweiterte Rechte + Aufsicht",
    "evt_operator":       "EVT-Operator – Eigener Status, eigene Einsätze, GPS",
    "beobachter":         "Beobachter – Nur Lesezugriff auf Lagekarte",
    "aerztlicher_leiter": "Ärztlicher Leiter – Medizinische Qualitätsdaten",
    "datenschutz":        "Datenschutzbeauftragter – Audit-Logs, Verarbeitungsverzeichnisse",
}

# Hierarchie: höhere Stufe enthält niedrigere Rechte
ROLE_HIERARCHY = {
    "admin": 100,
    "schichtleiter": 80,
    "disponent": 60,
    "aerztlicher_leiter": 50,
    "datenschutz": 50,
    "evt_operator": 30,
    "beobachter": 10,
}


class User(UserMixin, db.Model):
    """Benutzer mit Authentifizierung und Rollenzuweisung."""
    __tablename__ = "users"

    id             = db.Column(db.Integer,     primary_key=True)
    username       = db.Column(db.String(80),  nullable=False, unique=True, index=True)
    password_hash  = db.Column(db.String(255), nullable=False)
    role           = db.Column(db.String(30),  nullable=False, default="beobachter")
    display_name   = db.Column(db.String(120), nullable=True)

    is_active_user = db.Column(db.Boolean,     nullable=False, default=True)
    is_locked      = db.Column(db.Boolean,     nullable=False, default=False)
    failed_logins  = db.Column(db.Integer,     nullable=False, default=0)
    locked_until   = db.Column(db.DateTime,    nullable=True)

    last_login     = db.Column(db.DateTime,    nullable=True)
    created_at     = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    # MFA (TOTP)
    mfa_secret     = db.Column(db.String(32),  nullable=True)
    mfa_enabled    = db.Column(db.Boolean,     nullable=False, default=False)

    # Access Review
    last_review_at = db.Column(db.DateTime,    nullable=True)

    @property
    def is_active(self):
        return self.is_active_user and not self.is_locked

    def set_password(self, password: str):
        import bcrypt
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        import bcrypt
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    def has_role(self, required_role: str) -> bool:
        user_level = ROLE_HIERARCHY.get(self.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    def has_any_role(self, *roles: str) -> bool:
        return self.role in roles or any(self.has_role(r) for r in roles)

    # ── MFA (TOTP) ───────────────────────────────────────────────
    def generate_mfa_secret(self):
        """Generates and stores a new TOTP secret."""
        import pyotp
        self.mfa_secret = pyotp.random_base32()
        return self.mfa_secret

    def verify_mfa(self, token: str) -> bool:
        """Verifies a TOTP token against the stored secret."""
        if not self.mfa_secret:
            return False
        import pyotp
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token)

    def get_mfa_provisioning_uri(self, issuer: str = "OpMan-GPT") -> str:
        """Returns an otpauth:// URI for QR code generation."""
        if not self.mfa_secret:
            return ""
        import pyotp
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.provisioning_uri(name=self.username, issuer_name=issuer)


class AuditLog(db.Model):
    """Revisionssicheres Audit-Log für alle sicherheitsrelevanten Aktionen."""
    __tablename__ = "audit_log"

    id           = db.Column(db.Integer,     primary_key=True)
    timestamp    = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow, index=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=True)
    username     = db.Column(db.String(80),  nullable=True)
    action       = db.Column(db.String(50),  nullable=False, index=True)
    resource     = db.Column(db.String(80),  nullable=True)
    resource_id  = db.Column(db.String(50),  nullable=True)
    details      = db.Column(db.Text,        nullable=True)
    ip_address   = db.Column(db.String(45),  nullable=True)
    user_agent   = db.Column(db.String(300), nullable=True)
    hash         = db.Column(db.String(64),  nullable=True)


class UserSession(db.Model):
    """Active user sessions for session limiting (max 1 per user)."""
    __tablename__ = "user_sessions"

    id         = db.Column(db.Integer,     primary_key=True)
    user_id    = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False, index=True)
    session_id = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    last_seen  = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45),  nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)

    user = db.relationship("User", backref=db.backref("sessions", cascade="all, delete-orphan"))


class BreakGlassLog(db.Model):
    """Audit log for break-glass emergency access elevation."""
    __tablename__ = "break_glass_log"

    id          = db.Column(db.Integer,     primary_key=True)
    user_id     = db.Column(db.Integer,     db.ForeignKey("users.id"), nullable=False)
    timestamp   = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    reason      = db.Column(db.Text,        nullable=False)
    approved_by = db.Column(db.String(80),  nullable=True)
    expires_at  = db.Column(db.DateTime,    nullable=False)

    user = db.relationship("User", backref=db.backref("break_glass_logs", cascade="all, delete-orphan"))


class CaseDoc(db.Model):
    """Dokumentation eines Übungsfalls (P1–P6)."""
    __tablename__ = "case_docs"

    id = db.Column(db.String(5), primary_key=True)   # 'P1' … 'P6'

    assigned_evt   = db.Column(db.String(20),  nullable=True)   # z.B. "EVT 3"
    alarm_time     = db.Column(db.DateTime,    nullable=True)
    status3_time   = db.Column(db.DateTime,    nullable=True)
    status4_time   = db.Column(db.DateTime,    nullable=True)
    status7_time   = db.Column(db.DateTime,    nullable=True)
    status8_time   = db.Column(db.DateTime,    nullable=True)

    rmi_reported   = db.Column(db.String(20),  nullable=True)
    sk_reported    = db.Column(db.String(5),   nullable=True)
    pzc_reported   = db.Column(db.String(20),  nullable=True)
    abcde_schema   = db.Column(db.Text,        nullable=True)   # ABCDE-Schema bei SK1
    zielklinik     = db.Column(db.String(120), nullable=True)

    notes          = db.Column(db.Text,        nullable=True)
    completed      = db.Column(db.Boolean,     nullable=False, default=False)
    # JSON-Liste der EVT-Namen die diesen Fall bereits abgeschlossen haben, z.B. '["EVT 1","EVT 3"]'
    completed_evts = db.Column(db.Text,        nullable=False, default="[]")

    updated_at     = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)


class RadioLogEntry(db.Model):
    """Einzelner Eintrag im Funkprotokoll."""
    __tablename__ = "radio_log"

    id         = db.Column(db.Integer,  primary_key=True)
    timestamp  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sender     = db.Column(db.String(50), nullable=False)
    receiver   = db.Column(db.String(50), nullable=True)
    fms_status = db.Column(db.Integer,  nullable=True)
    case_ref   = db.Column(db.String(5), nullable=True)   # 'P1' … 'P6'
    message    = db.Column(db.Text,     nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Team(db.Model):
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)
    callsign = db.Column(db.String(50), nullable=True)

    # Verfügbarkeit (für Disposition)
    availability = db.Column(db.String(30), nullable=False, default="verfügbar")
    # verfügbar | bedingt | nicht_verfügbar

    # Funkstatus-Code (auch 0, 41, 51, 61, 62, 68, 69, 71, 77)
    radio_status = db.Column(db.Integer, nullable=False, default=1)

    # Funkgruppe: "regelfunk" | "bettenkanal"
    radio_group = db.Column(db.String(30), nullable=False, default="regelfunk")

    color = db.Column(db.String(12), nullable=False, default="#4ea1ff")

    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    gps_updated_at  = db.Column(db.DateTime, nullable=True)   # gesetzt wenn GPS vom EVT-Gerät kommt

    test_alarm_at   = db.Column(db.DateTime,   nullable=True)   # Testalarm-Zeitpunkt
    test_alarm_text = db.Column(db.String(200), nullable=True)   # Testalarm-Nachricht

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Mission(db.Model):
    __tablename__ = "missions"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)

    priority = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(50), nullable=False, default="offen")

    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)

    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey("missions.id"), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    team = db.relationship("Team", backref=db.backref("assignments", cascade="all, delete-orphan"))
    mission = db.relationship("Mission", backref=db.backref("assignments", cascade="all, delete-orphan"))


class ExerciseConfig(db.Model):
    """Globale Übungskonfiguration (Singleton, id=1)."""
    __tablename__ = "exercise_config"
    id = db.Column(db.Integer, primary_key=True)
    evt_count = db.Column(db.Integer, nullable=False, default=6)


class CaseDefinition(db.Model):
    """Vollständige Definition eines Übungsfalls (editierbar, JSON-importierbar)."""
    __tablename__ = "case_definitions"

    id            = db.Column(db.String(10),  primary_key=True)   # z.B. 'P1'
    schlagwort    = db.Column(db.String(200), nullable=False, default="")
    szenario      = db.Column(db.String(200), nullable=True)       # Untertitel Karte

    patient       = db.Column(db.String(100), nullable=False, default="")
    patient_alarm = db.Column(db.String(100), nullable=True)       # falscher Name
    alter         = db.Column(db.Integer,     nullable=True)
    geschlecht    = db.Column(db.String(1),   nullable=True)       # m / w / d

    w3w           = db.Column(db.String(120), nullable=True)       # echter Fundort
    w3w_alarm     = db.Column(db.String(120), nullable=True)       # falsche Alarmadresse
    lat           = db.Column(db.Float,       nullable=True)
    lng           = db.Column(db.Float,       nullable=True)

    # Auswertungsfelder
    rmi_soll      = db.Column(db.String(20),  nullable=True)
    sk_soll       = db.Column(db.String(20),  nullable=True)
    pzc_soll      = db.Column(db.String(50),  nullable=True)
    kein_transport= db.Column(db.Boolean,     nullable=False, default=False)

    # Medizinische Inhalte als JSON-Text
    vitals_json   = db.Column(db.Text, nullable=True)  # {"RR":"82/54","HF":"132",...}
    befund_json   = db.Column(db.Text, nullable=True)  # ["Bullet 1","Bullet 2",...]
    abcde_json    = db.Column(db.Text, nullable=True)  # {"A":"...","B":"...",...}
    sampler_json  = db.Column(db.Text, nullable=True)  # {"S":"...","A":"...",...}

    besonderheit  = db.Column(db.Text, nullable=True)  # Hinweis für EL / Mime
    hinweis       = db.Column(db.Text, nullable=True)  # extra Instruktionstext

    active        = db.Column(db.Boolean,     nullable=False, default=True)  # für diese Übung aktiv?

    sort_order    = db.Column(db.Integer, nullable=False, default=0)
    updated_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ── Convenience-Properties ──────────────────────────────────────
    import json as _json

    @property
    def vitals(self):
        try: return self._json.loads(self.vitals_json) if self.vitals_json else {}
        except Exception: return {}

    @property
    def befund(self):
        try: return self._json.loads(self.befund_json) if self.befund_json else []
        except Exception: return []

    @property
    def abcde(self):
        try: return self._json.loads(self.abcde_json) if self.abcde_json else {}
        except Exception: return {}

    @property
    def sampler(self):
        try: return self._json.loads(self.sampler_json) if self.sampler_json else {}
        except Exception: return {}

    def to_dict(self):
        return {
            "id": self.id, "schlagwort": self.schlagwort, "szenario": self.szenario,
            "patient": self.patient, "patient_alarm": self.patient_alarm,
            "alter": self.alter, "geschlecht": self.geschlecht,
            "w3w": self.w3w, "w3w_alarm": self.w3w_alarm, "lat": self.lat, "lng": self.lng,
            "rmi_soll": self.rmi_soll, "sk_soll": self.sk_soll, "pzc_soll": self.pzc_soll,
            "kein_transport": self.kein_transport,
            "vitals": self.vitals, "befund": self.befund,
            "abcde": self.abcde, "sampler": self.sampler,
            "besonderheit": self.besonderheit, "hinweis": self.hinweis,
        }


class PushSubscription(db.Model):
    """Web-Push-Abonnement eines EVT-Geräts."""
    __tablename__ = "push_subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    evt_name   = db.Column(db.String(30), nullable=False)            # z.B. "EVT 1"
    endpoint   = db.Column(db.Text,       nullable=False, unique=True)
    p256dh     = db.Column(db.Text,       nullable=False)
    auth       = db.Column(db.Text,       nullable=False)
    created_at = db.Column(db.DateTime,   nullable=False, default=datetime.utcnow)


class PseudonymMapping(db.Model):
    """Mapping between original data hashes and pseudonyms (Art. 4 Nr. 5 DSGVO)."""
    __tablename__ = "pseudonym_mappings"

    id            = db.Column(db.Integer,     primary_key=True)
    original_hash = db.Column(db.String(128), nullable=False, unique=True, index=True)
    pseudonym     = db.Column(db.String(120), nullable=False)
    created_at    = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)


class ConsentRecord(db.Model):
    """Einwilligungsverwaltung gemäß Art. 6/7 DSGVO."""
    __tablename__ = "consent_records"

    id            = db.Column(db.Integer,     primary_key=True)
    data_subject  = db.Column(db.String(200), nullable=False, index=True)
    purpose       = db.Column(db.String(300), nullable=False)
    granted_at    = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    withdrawn_at  = db.Column(db.DateTime,    nullable=True)
    legal_basis   = db.Column(db.String(100), nullable=False, default="Einwilligung Art. 6(1)(a)")