from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


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


class CaseEvtResult(db.Model):
    """Gespeichertes Auswertungsergebnis pro Fall + EVT-Team.
    Wird automatisch erstellt, wenn ein EVT gewechselt oder ein Fall
    abgeschlossen wird, damit frühere Ergebnisse nicht verloren gehen."""
    __tablename__ = "case_evt_results"
    __table_args__ = (
        db.UniqueConstraint("case_id", "evt_name", name="uq_case_evt"),
    )

    id             = db.Column(db.Integer, primary_key=True)
    case_id        = db.Column(db.String(5),   nullable=False)   # P1 … P9
    evt_name       = db.Column(db.String(20),  nullable=False)   # z.B. "EVT 3"

    pzc_reported   = db.Column(db.String(20),  nullable=True)
    abcde_schema   = db.Column(db.Text,        nullable=True)
    zielklinik     = db.Column(db.String(120), nullable=True)
    notes          = db.Column(db.Text,        nullable=True)

    alarm_time     = db.Column(db.DateTime,    nullable=True)
    status3_time   = db.Column(db.DateTime,    nullable=True)
    status4_time   = db.Column(db.DateTime,    nullable=True)
    status7_time   = db.Column(db.DateTime,    nullable=True)
    status8_time   = db.Column(db.DateTime,    nullable=True)

    created_at     = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)


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
    marked     = db.Column(db.Boolean,  nullable=False, default=False)
    note       = db.Column(db.Text,     nullable=True)
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
    base_url = db.Column(db.String(300), nullable=True, default="")
    admin_pin = db.Column(db.String(4), nullable=False, default="1234")


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

    abcd_soll_json = db.Column(db.Text, nullable=True)  # {"A":1,"B":2,"C":4,"D":2}
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
    def abcd_soll(self):
        try: return self._json.loads(self.abcd_soll_json) if self.abcd_soll_json else {}
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
            "abcde": self.abcde, "abcd_soll": self.abcd_soll, "sampler": self.sampler,
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