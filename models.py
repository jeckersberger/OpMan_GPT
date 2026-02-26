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
    zielklinik     = db.Column(db.String(120), nullable=True)

    notes          = db.Column(db.Text,        nullable=True)
    completed      = db.Column(db.Boolean,     nullable=False, default=False)

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

    color = db.Column(db.String(12), nullable=False, default="#4ea1ff")

    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

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