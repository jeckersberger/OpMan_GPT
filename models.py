from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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