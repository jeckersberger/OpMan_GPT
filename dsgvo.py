"""DSGVO-Compliance & Datenverschlüsselung für OpMan-GPT.

Implementiert:
- Feld-Level-Verschlüsselung (Fernet / AES-128-CBC)
- Recht auf Löschung (Art. 17 DSGVO)
- Datenportabilität (Art. 20 DSGVO)
- Pseudonymisierung (Art. 4 Nr. 5 DSGVO)
- Datenminimierungsbericht
- Breach-Erkennung
- Einwilligungsverwaltung (Art. 6/7 DSGVO)
- DSGVO-Dashboard
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from datetime import datetime, timezone, timedelta

from flask import (
    Blueprint, request, jsonify, current_app,
    render_template_string, flash, redirect, url_for,
)
from flask_login import login_required, current_user

from auth import role_required, audit_log
from models import (
    db, CaseDefinition, CaseDoc, AuditLog,
    PseudonymMapping, ConsentRecord,
)

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------
dsgvo_bp = Blueprint("dsgvo", __name__)

# Erlaubte Rollen für DSGVO-Endpunkte
DSGVO_ROLES = ("admin", "datenschutz", "schichtleiter")

# Standardaufbewahrungsfrist in Tagen
DEFAULT_RETENTION_DAYS = 365


# ═══════════════════════════════════════════════════════════════════════════
#  1. Feld-Level-Verschlüsselung (Fernet)
# ═══════════════════════════════════════════════════════════════════════════
_fernet_instance = None


def _get_key_path() -> str:
    """Returns the path to the encryption key file."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "instance", "encryption.key")


def _ensure_encryption_key() -> bytes:
    """Loads or creates the Fernet encryption key."""
    key_path = _get_key_path()
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read().strip()
    # Auto-generate
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(key)
    return key


def _get_fernet():
    """Returns a cached Fernet instance."""
    global _fernet_instance
    if _fernet_instance is None:
        from cryptography.fernet import Fernet
        _fernet_instance = Fernet(_ensure_encryption_key())
    return _fernet_instance


def encrypt_field(value: str, key: bytes = None) -> str:
    """Encrypts a string value using Fernet and returns a base64-encoded token.

    Args:
        value: The plaintext string to encrypt.
        key: Optional Fernet key bytes. If None, uses the auto-managed key.

    Returns:
        The encrypted token as a UTF-8 string.
    """
    if value is None:
        return None
    if key is not None:
        from cryptography.fernet import Fernet
        f = Fernet(key)
    else:
        f = _get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_field(token: str, key: bytes = None) -> str:
    """Decrypts a Fernet token back to its original string value.

    Args:
        token: The encrypted token string.
        key: Optional Fernet key bytes. If None, uses the auto-managed key.

    Returns:
        The decrypted plaintext string.
    """
    if token is None:
        return None
    if key is not None:
        from cryptography.fernet import Fernet
        f = Fernet(key)
    else:
        f = _get_fernet()
    return f.decrypt(token.encode("utf-8")).decode("utf-8")


def encrypt_patient_name(case: CaseDefinition) -> None:
    """Encrypts the patient and patient_alarm fields of a CaseDefinition in-place."""
    if case.patient and not case.patient.startswith("gAAAAA"):
        case.patient = encrypt_field(case.patient)
    if case.patient_alarm and not case.patient_alarm.startswith("gAAAAA"):
        case.patient_alarm = encrypt_field(case.patient_alarm)


def decrypt_patient_name(case: CaseDefinition) -> dict:
    """Returns a dict with decrypted patient fields (non-destructive)."""
    result = {}
    try:
        result["patient"] = decrypt_field(case.patient) if case.patient and case.patient.startswith("gAAAAA") else case.patient
    except Exception:
        result["patient"] = case.patient
    try:
        result["patient_alarm"] = decrypt_field(case.patient_alarm) if case.patient_alarm and case.patient_alarm.startswith("gAAAAA") else case.patient_alarm
    except Exception:
        result["patient_alarm"] = case.patient_alarm
    return result


# ═══════════════════════════════════════════════════════════════════════════
#  Helper
# ═══════════════════════════════════════════════════════════════════════════

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_retention_days() -> int:
    return current_app.config.get("DSGVO_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)


# ═══════════════════════════════════════════════════════════════════════════
#  2. Recht auf Löschung / Anonymisierung (Art. 17 DSGVO)
# ═══════════════════════════════════════════════════════════════════════════

@dsgvo_bp.route("/api/dsgvo/personal-data/<case_id>", methods=["DELETE"])
@role_required(*DSGVO_ROLES)
def delete_personal_data(case_id):
    """Anonymisiert einen Einzelfall (Art. 17 DSGVO – Recht auf Löschung)."""
    case = CaseDefinition.query.get(case_id)
    if not case:
        return jsonify({"error": "Fall nicht gefunden"}), 404

    # Anonymisieren
    case.patient = "GELÖSCHT"
    case.patient_alarm = "GELÖSCHT"
    case.alter = None
    case.geschlecht = None
    case.besonderheit = None
    case.hinweis = None
    case.updated_at = _utcnow()

    audit_log(
        "DSGVO_ERASURE",
        resource="case_definition",
        resource_id=case_id,
        details=f"Personenbezogene Daten anonymisiert (Art. 17 DSGVO)",
    )
    db.session.commit()
    return jsonify({"status": "ok", "message": f"Fall {case_id} anonymisiert"})


@dsgvo_bp.route("/api/dsgvo/auto-cleanup", methods=["POST"])
@role_required(*DSGVO_ROLES)
def auto_cleanup():
    """Automatische Bereinigung von Daten älter als die Aufbewahrungsfrist."""
    retention_days = request.json.get("retention_days", _get_retention_days()) if request.is_json else _get_retention_days()
    cutoff = _utcnow() - timedelta(days=int(retention_days))

    # Alte Fälle anonymisieren
    old_cases = CaseDefinition.query.filter(CaseDefinition.updated_at < cutoff).all()
    count = 0
    for case in old_cases:
        if case.patient and case.patient != "GELÖSCHT":
            case.patient = "GELÖSCHT"
            case.patient_alarm = "GELÖSCHT"
            case.alter = None
            case.geschlecht = None
            case.besonderheit = None
            case.hinweis = None
            case.updated_at = _utcnow()
            count += 1

    # Alte Audit-Logs entfernen (nur Details, Struktur bleibt)
    old_logs = AuditLog.query.filter(AuditLog.timestamp < cutoff).all()
    log_count = 0
    for log in old_logs:
        if log.details:
            log.details = "[BEREINIGT]"
            log_count += 1

    audit_log(
        "DSGVO_AUTO_CLEANUP",
        resource="system",
        details=f"Aufbewahrungsfrist: {retention_days} Tage. "
                f"{count} Fälle anonymisiert, {log_count} Log-Details bereinigt.",
    )
    db.session.commit()
    return jsonify({
        "status": "ok",
        "cases_anonymized": count,
        "logs_cleaned": log_count,
        "retention_days": retention_days,
        "cutoff_date": cutoff.isoformat(),
    })


# ═══════════════════════════════════════════════════════════════════════════
#  3. Datenportabilität (Art. 20 DSGVO)
# ═══════════════════════════════════════════════════════════════════════════

@dsgvo_bp.route("/api/dsgvo/export/<case_id>", methods=["GET"])
@role_required(*DSGVO_ROLES)
def export_case(case_id):
    """Vollständiger JSON-Export aller personenbezogenen Daten eines Falls."""
    case = CaseDefinition.query.get(case_id)
    if not case:
        return jsonify({"error": "Fall nicht gefunden"}), 404

    # Decrypt patient names for export
    decrypted = decrypt_patient_name(case)

    export_data = {
        "meta": {
            "export_type": "DSGVO Art. 20 – Datenportabilität",
            "exported_at": _utcnow().isoformat(),
            "exported_by": current_user.username,
            "case_id": case_id,
        },
        "personal_data": {
            "patient": decrypted.get("patient", case.patient),
            "patient_alarm": decrypted.get("patient_alarm", case.patient_alarm),
            "alter": case.alter,
            "geschlecht": case.geschlecht,
        },
        "case_data": case.to_dict(),
    }

    # Include linked CaseDoc if it exists
    case_doc = CaseDoc.query.get(case_id)
    if case_doc:
        export_data["documentation"] = {
            "assigned_evt": case_doc.assigned_evt,
            "alarm_time": case_doc.alarm_time.isoformat() if case_doc.alarm_time else None,
            "status3_time": case_doc.status3_time.isoformat() if case_doc.status3_time else None,
            "status4_time": case_doc.status4_time.isoformat() if case_doc.status4_time else None,
            "status7_time": case_doc.status7_time.isoformat() if case_doc.status7_time else None,
            "status8_time": case_doc.status8_time.isoformat() if case_doc.status8_time else None,
            "rmi_reported": case_doc.rmi_reported,
            "sk_reported": case_doc.sk_reported,
            "pzc_reported": case_doc.pzc_reported,
            "zielklinik": case_doc.zielklinik,
            "notes": case_doc.notes,
        }

    audit_log(
        "DSGVO_EXPORT",
        resource="case_definition",
        resource_id=case_id,
        details="Einzelfall-Export (Art. 20 DSGVO)",
    )
    db.session.commit()
    return jsonify(export_data)


@dsgvo_bp.route("/api/dsgvo/export-all", methods=["GET"])
@role_required(*DSGVO_ROLES)
def export_all():
    """Export ALLER personenbezogenen Daten (für DSB / Datenschutzbeauftragten)."""
    cases = CaseDefinition.query.all()
    exported = []
    for case in cases:
        decrypted = decrypt_patient_name(case)
        entry = case.to_dict()
        entry["patient"] = decrypted.get("patient", case.patient)
        entry["patient_alarm"] = decrypted.get("patient_alarm", case.patient_alarm)
        exported.append(entry)

    # Consent records
    consents = ConsentRecord.query.all()
    consent_data = [{
        "id": c.id,
        "data_subject": c.data_subject,
        "purpose": c.purpose,
        "granted_at": c.granted_at.isoformat() if c.granted_at else None,
        "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
        "legal_basis": c.legal_basis,
    } for c in consents]

    export_data = {
        "meta": {
            "export_type": "DSGVO Gesamtexport – Datenschutzbeauftragter",
            "exported_at": _utcnow().isoformat(),
            "exported_by": current_user.username,
            "total_cases": len(exported),
            "total_consents": len(consent_data),
        },
        "cases": exported,
        "consent_records": consent_data,
    }

    audit_log(
        "DSGVO_EXPORT_ALL",
        resource="system",
        details=f"Gesamtexport: {len(exported)} Fälle, {len(consent_data)} Einwilligungen",
    )
    db.session.commit()
    return jsonify(export_data)


# ═══════════════════════════════════════════════════════════════════════════
#  4. Pseudonymisierung (Art. 4 Nr. 5 DSGVO)
# ═══════════════════════════════════════════════════════════════════════════

def _generate_pseudonym() -> str:
    """Generates a human-readable pseudonym like 'Patient-A7F3'."""
    return f"Patient-{uuid.uuid4().hex[:6].upper()}"


@dsgvo_bp.route("/api/dsgvo/pseudonymize/<case_id>", methods=["POST"])
@role_required(*DSGVO_ROLES)
def pseudonymize_case(case_id):
    """Ersetzt echte Namen durch Pseudonyme, speichert Mapping getrennt."""
    case = CaseDefinition.query.get(case_id)
    if not case:
        return jsonify({"error": "Fall nicht gefunden"}), 404

    results = {}

    for field_name in ("patient", "patient_alarm"):
        original_value = getattr(case, field_name)
        if not original_value or original_value in ("GELÖSCHT", ""):
            continue

        # Hash the original value for the mapping
        original_hash = hashlib.sha256(original_value.encode("utf-8")).hexdigest()

        # Check if mapping already exists
        existing = PseudonymMapping.query.filter_by(original_hash=original_hash).first()
        if existing:
            pseudonym = existing.pseudonym
        else:
            pseudonym = _generate_pseudonym()
            mapping = PseudonymMapping(
                original_hash=original_hash,
                pseudonym=pseudonym,
                created_at=_utcnow(),
            )
            db.session.add(mapping)

        setattr(case, field_name, pseudonym)
        results[field_name] = pseudonym

    case.updated_at = _utcnow()

    audit_log(
        "DSGVO_PSEUDONYMIZE",
        resource="case_definition",
        resource_id=case_id,
        details=f"Felder pseudonymisiert: {', '.join(results.keys())}",
    )
    db.session.commit()
    return jsonify({
        "status": "ok",
        "case_id": case_id,
        "pseudonymized_fields": results,
    })


# ═══════════════════════════════════════════════════════════════════════════
#  5. Datenminimierungsbericht
# ═══════════════════════════════════════════════════════════════════════════

DATA_FIELDS_REGISTRY = [
    {
        "model": "CaseDefinition",
        "field": "patient",
        "purpose": "Identifikation des Patienten im Übungsszenario",
        "legal_basis": "Art. 6(1)(f) DSGVO – Berechtigtes Interesse (Übungsdurchführung)",
        "retention": "Bis Ende der Aufbewahrungsfrist oder Löschantrag",
        "category": "Personenbezogene Daten",
    },
    {
        "model": "CaseDefinition",
        "field": "patient_alarm",
        "purpose": "Alarmierungsname (ggf. abweichend vom echten Namen)",
        "legal_basis": "Art. 6(1)(f) DSGVO – Berechtigtes Interesse",
        "retention": "Bis Ende der Aufbewahrungsfrist oder Löschantrag",
        "category": "Personenbezogene Daten",
    },
    {
        "model": "CaseDefinition",
        "field": "alter",
        "purpose": "Alter des Patienten für medizinische Szenarien",
        "legal_basis": "Art. 6(1)(f) DSGVO – Berechtigtes Interesse",
        "retention": "Bis Ende der Aufbewahrungsfrist oder Löschantrag",
        "category": "Gesundheitsdaten (Art. 9)",
    },
    {
        "model": "CaseDefinition",
        "field": "geschlecht",
        "purpose": "Geschlecht des Patienten für medizinische Szenarien",
        "legal_basis": "Art. 6(1)(f) DSGVO – Berechtigtes Interesse",
        "retention": "Bis Ende der Aufbewahrungsfrist oder Löschantrag",
        "category": "Personenbezogene Daten",
    },
    {
        "model": "CaseDefinition",
        "field": "vitals_json",
        "purpose": "Vitalparameter für Übungsdokumentation",
        "legal_basis": "Art. 6(1)(f) DSGVO – Berechtigtes Interesse",
        "retention": "Bis Ende der Aufbewahrungsfrist",
        "category": "Gesundheitsdaten (Art. 9)",
    },
    {
        "model": "User",
        "field": "username",
        "purpose": "Benutzeridentifikation und Authentifizierung",
        "legal_basis": "Art. 6(1)(b) DSGVO – Vertragserfüllung",
        "retention": "Solange Benutzerkonto aktiv",
        "category": "Personenbezogene Daten",
    },
    {
        "model": "AuditLog",
        "field": "username / ip_address",
        "purpose": "Revisionssichere Protokollierung sicherheitsrelevanter Aktionen",
        "legal_basis": "Art. 6(1)(c) DSGVO – Rechtliche Verpflichtung",
        "retention": "Gesetzliche Aufbewahrungsfrist (mind. 1 Jahr)",
        "category": "Nutzungsdaten",
    },
    {
        "model": "ConsentRecord",
        "field": "data_subject",
        "purpose": "Dokumentation erteilter Einwilligungen",
        "legal_basis": "Art. 7(1) DSGVO – Nachweispflicht",
        "retention": "3 Jahre nach Widerruf der Einwilligung",
        "category": "Einwilligungsdaten",
    },
]


@dsgvo_bp.route("/api/dsgvo/minimization-report", methods=["GET"])
@role_required(*DSGVO_ROLES)
def minimization_report():
    """Datenminimierungsbericht: Alle gespeicherten Datenfelder mit Zweck und Frist."""
    retention_days = _get_retention_days()

    report = {
        "meta": {
            "report_type": "Datenminimierungsbericht (Art. 5(1)(c) DSGVO)",
            "generated_at": _utcnow().isoformat(),
            "retention_period_days": retention_days,
            "generated_by": current_user.username,
        },
        "fields": DATA_FIELDS_REGISTRY,
        "statistics": {
            "total_cases": CaseDefinition.query.count(),
            "anonymized_cases": CaseDefinition.query.filter_by(patient="GELÖSCHT").count(),
            "active_cases": CaseDefinition.query.filter(CaseDefinition.patient != "GELÖSCHT").count(),
            "pseudonym_mappings": PseudonymMapping.query.count(),
            "consent_records": ConsentRecord.query.count(),
            "active_consents": ConsentRecord.query.filter(ConsentRecord.withdrawn_at.is_(None)).count(),
        },
    }

    audit_log(
        "DSGVO_MINIMIZATION_REPORT",
        resource="system",
        details="Datenminimierungsbericht erstellt",
    )
    db.session.commit()
    return jsonify(report)


# ═══════════════════════════════════════════════════════════════════════════
#  6. Breach-Erkennung
# ═══════════════════════════════════════════════════════════════════════════

@dsgvo_bp.route("/api/dsgvo/check-breach", methods=["POST"])
@role_required(*DSGVO_ROLES)
def check_breach():
    """Prüft auf Indikatoren einer Datenschutzverletzung."""
    hours = 24
    if request.is_json and request.json.get("hours"):
        hours = int(request.json["hours"])
    since = _utcnow() - timedelta(hours=hours)

    indicators = []

    # 1. Ungewöhnliches Export-Volumen
    export_count = AuditLog.query.filter(
        AuditLog.timestamp >= since,
        AuditLog.action.in_(["DSGVO_EXPORT", "DSGVO_EXPORT_ALL"]),
    ).count()
    if export_count > 10:
        indicators.append({
            "type": "EXCESSIVE_EXPORTS",
            "severity": "HIGH" if export_count > 50 else "MEDIUM",
            "description": f"{export_count} Datenexporte in den letzten {hours} Stunden",
            "count": export_count,
        })

    # 2. Massen-Datenzugriffe
    data_access_count = AuditLog.query.filter(
        AuditLog.timestamp >= since,
        AuditLog.action.in_(["API_CALL", "DATA_ACCESS", "DSGVO_EXPORT", "DSGVO_EXPORT_ALL"]),
    ).count()
    if data_access_count > 100:
        indicators.append({
            "type": "MASS_DATA_ACCESS",
            "severity": "HIGH" if data_access_count > 500 else "MEDIUM",
            "description": f"{data_access_count} Datenzugriffe in den letzten {hours} Stunden",
            "count": data_access_count,
        })

    # 3. Unautorisierte Zugriffsversuche
    denied_count = AuditLog.query.filter(
        AuditLog.timestamp >= since,
        AuditLog.action == "ACCESS_DENIED",
    ).count()
    if denied_count > 5:
        indicators.append({
            "type": "UNAUTHORIZED_ACCESS_ATTEMPTS",
            "severity": "CRITICAL" if denied_count > 20 else "HIGH",
            "description": f"{denied_count} abgelehnte Zugriffsversuche in den letzten {hours} Stunden",
            "count": denied_count,
        })

    # 4. Fehlgeschlagene Logins
    failed_logins = AuditLog.query.filter(
        AuditLog.timestamp >= since,
        AuditLog.action == "LOGIN_FAILED",
    ).count()
    if failed_logins > 10:
        indicators.append({
            "type": "BRUTE_FORCE_ATTEMPT",
            "severity": "CRITICAL" if failed_logins > 50 else "HIGH",
            "description": f"{failed_logins} fehlgeschlagene Logins in den letzten {hours} Stunden",
            "count": failed_logins,
        })

    # 5. Ungewöhnliche Löschungen
    erasure_count = AuditLog.query.filter(
        AuditLog.timestamp >= since,
        AuditLog.action == "DSGVO_ERASURE",
    ).count()
    if erasure_count > 5:
        indicators.append({
            "type": "MASS_DELETION",
            "severity": "MEDIUM",
            "description": f"{erasure_count} Datenlöschungen in den letzten {hours} Stunden",
            "count": erasure_count,
        })

    overall_severity = "NONE"
    if indicators:
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        overall_severity = max(indicators, key=lambda x: severity_order.get(x["severity"], 0))["severity"]

    audit_log(
        "DSGVO_BREACH_CHECK",
        resource="system",
        details=f"Breach-Check: {len(indicators)} Indikatoren, Schweregrad: {overall_severity}",
    )
    db.session.commit()

    return jsonify({
        "status": "ok",
        "check_period_hours": hours,
        "checked_at": _utcnow().isoformat(),
        "overall_severity": overall_severity,
        "indicators": indicators,
        "breach_detected": overall_severity in ("HIGH", "CRITICAL"),
    })


# ═══════════════════════════════════════════════════════════════════════════
#  7. Einwilligungsverwaltung (Art. 6/7 DSGVO)
# ═══════════════════════════════════════════════════════════════════════════

@dsgvo_bp.route("/api/dsgvo/consent", methods=["GET"])
@role_required(*DSGVO_ROLES)
def list_consents():
    """Alle Einwilligungseinträge auflisten."""
    consents = ConsentRecord.query.order_by(ConsentRecord.granted_at.desc()).all()
    return jsonify([{
        "id": c.id,
        "data_subject": c.data_subject,
        "purpose": c.purpose,
        "granted_at": c.granted_at.isoformat() if c.granted_at else None,
        "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
        "legal_basis": c.legal_basis,
        "active": c.withdrawn_at is None,
    } for c in consents])


@dsgvo_bp.route("/api/dsgvo/consent", methods=["POST"])
@role_required(*DSGVO_ROLES)
def create_consent():
    """Neue Einwilligung erfassen."""
    data = request.get_json(force=True)
    if not data.get("data_subject") or not data.get("purpose"):
        return jsonify({"error": "data_subject und purpose sind Pflichtfelder"}), 400

    record = ConsentRecord(
        data_subject=data["data_subject"],
        purpose=data["purpose"],
        legal_basis=data.get("legal_basis", "Einwilligung Art. 6(1)(a)"),
        granted_at=_utcnow(),
    )
    db.session.add(record)

    audit_log(
        "DSGVO_CONSENT_CREATED",
        resource="consent_record",
        details=f"Einwilligung erstellt: {data['data_subject']} – {data['purpose']}",
    )
    db.session.commit()
    return jsonify({"status": "ok", "id": record.id}), 201


@dsgvo_bp.route("/api/dsgvo/consent/<int:consent_id>", methods=["GET"])
@role_required(*DSGVO_ROLES)
def get_consent(consent_id):
    """Einzelne Einwilligung abrufen."""
    c = ConsentRecord.query.get(consent_id)
    if not c:
        return jsonify({"error": "Einwilligung nicht gefunden"}), 404
    return jsonify({
        "id": c.id,
        "data_subject": c.data_subject,
        "purpose": c.purpose,
        "granted_at": c.granted_at.isoformat() if c.granted_at else None,
        "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
        "legal_basis": c.legal_basis,
        "active": c.withdrawn_at is None,
    })


@dsgvo_bp.route("/api/dsgvo/consent/<int:consent_id>", methods=["PUT"])
@role_required(*DSGVO_ROLES)
def update_consent(consent_id):
    """Einwilligung aktualisieren."""
    c = ConsentRecord.query.get(consent_id)
    if not c:
        return jsonify({"error": "Einwilligung nicht gefunden"}), 404

    data = request.get_json(force=True)
    if "data_subject" in data:
        c.data_subject = data["data_subject"]
    if "purpose" in data:
        c.purpose = data["purpose"]
    if "legal_basis" in data:
        c.legal_basis = data["legal_basis"]

    audit_log(
        "DSGVO_CONSENT_UPDATED",
        resource="consent_record",
        resource_id=str(consent_id),
        details=f"Einwilligung aktualisiert",
    )
    db.session.commit()
    return jsonify({"status": "ok"})


@dsgvo_bp.route("/api/dsgvo/consent/<int:consent_id>/withdraw", methods=["POST"])
@role_required(*DSGVO_ROLES)
def withdraw_consent(consent_id):
    """Einwilligung widerrufen (Art. 7(3) DSGVO)."""
    c = ConsentRecord.query.get(consent_id)
    if not c:
        return jsonify({"error": "Einwilligung nicht gefunden"}), 404

    if c.withdrawn_at:
        return jsonify({"error": "Einwilligung bereits widerrufen"}), 409

    c.withdrawn_at = _utcnow()

    audit_log(
        "DSGVO_CONSENT_WITHDRAWN",
        resource="consent_record",
        resource_id=str(consent_id),
        details=f"Einwilligung widerrufen: {c.data_subject} – {c.purpose}",
    )
    db.session.commit()
    return jsonify({"status": "ok", "withdrawn_at": c.withdrawn_at.isoformat()})


@dsgvo_bp.route("/api/dsgvo/consent/<int:consent_id>", methods=["DELETE"])
@role_required(*DSGVO_ROLES)
def delete_consent(consent_id):
    """Einwilligungseintrag löschen."""
    c = ConsentRecord.query.get(consent_id)
    if not c:
        return jsonify({"error": "Einwilligung nicht gefunden"}), 404

    audit_log(
        "DSGVO_CONSENT_DELETED",
        resource="consent_record",
        resource_id=str(consent_id),
        details=f"Einwilligung gelöscht: {c.data_subject} – {c.purpose}",
    )
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "ok"})


# ═══════════════════════════════════════════════════════════════════════════
#  8. DSGVO-Dashboard
# ═══════════════════════════════════════════════════════════════════════════

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DSGVO-Dashboard – OpMan-GPT</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0d1117; color: #c9d1d9; line-height: 1.6; }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
  h1 { color: #58a6ff; margin-bottom: 8px; font-size: 1.6rem; }
  h2 { color: #8b949e; font-size: 1.1rem; margin-bottom: 20px; font-weight: 400; }
  h3 { color: #58a6ff; margin: 0 0 12px 0; font-size: 1.05rem; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin-bottom: 24px; }

  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 20px; transition: border-color 0.2s;
  }
  .card:hover { border-color: #58a6ff; }

  .stat-row { display: flex; justify-content: space-between; padding: 6px 0;
              border-bottom: 1px solid #21262d; }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { color: #8b949e; }
  .stat-value { color: #c9d1d9; font-weight: 600; }
  .stat-value.green { color: #3fb950; }
  .stat-value.yellow { color: #d29922; }
  .stat-value.red { color: #f85149; }

  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px;
           font-size: 0.8rem; font-weight: 600; }
  .badge-green { background: #1a3d1a; color: #3fb950; border: 1px solid #3fb950; }
  .badge-yellow { background: #3d2e0a; color: #d29922; border: 1px solid #d29922; }
  .badge-red { background: #3d1a1a; color: #f85149; border: 1px solid #f85149; }

  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #21262d; font-size: 0.9rem; }
  th { background: #161b22; font-weight: 600; color: #8b949e; }

  .btn { display: inline-block; padding: 8px 16px; border-radius: 6px; border: none;
         cursor: pointer; font-size: 0.85rem; font-weight: 600; text-decoration: none;
         transition: background 0.2s; margin: 4px 4px 4px 0; }
  .btn-primary { background: #238636; color: #fff; }
  .btn-primary:hover { background: #2ea043; }
  .btn-danger { background: #da3633; color: #fff; }
  .btn-danger:hover { background: #f85149; }
  .btn-info { background: #1f6feb; color: #fff; }
  .btn-info:hover { background: #388bfd; }

  .nav-bar {
    background: #161b22; border-bottom: 1px solid #30363d;
    padding: 10px 20px; margin-bottom: 24px; display: flex;
    align-items: center; gap: 16px;
  }
  .nav-bar a { color: #58a6ff; text-decoration: none; font-size: 0.9rem; }
  .nav-bar a:hover { text-decoration: underline; }

  .alert { padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 0.9rem; }
  .alert-success { background: #1a3d1a; border: 1px solid #22c55e; color: #86efac; }
  .alert-warning { background: #3d2e0a; border: 1px solid #d29922; color: #fcd34d; }
  .alert-danger { background: #3d1a1a; border: 1px solid #f85149; color: #fca5a5; }

  #result-box { margin-top: 16px; padding: 12px; background: #0d1117;
                border: 1px solid #30363d; border-radius: 6px;
                font-family: monospace; font-size: 0.85rem; white-space: pre-wrap;
                display: none; max-height: 400px; overflow-y: auto; }
</style>
</head>
<body>
<div class="nav-bar">
  <a href="/">OpMan-GPT</a>
  <a href="/dsgvo">DSGVO-Dashboard</a>
  <a href="/admin/users">Benutzerverwaltung</a>
  <span style="margin-left:auto; color:#8b949e;">{{ user.display_name or user.username }} ({{ user.role }})</span>
</div>

<div class="container">
<h1>DSGVO-Dashboard</h1>
<h2>Datenschutz-Grundverordnung – Technische und organisatorische Massnahmen</h2>

{% if breach_severity in ('HIGH', 'CRITICAL') %}
<div class="alert alert-danger">
  <strong>WARNUNG:</strong> Datenschutzverletzung erkannt! Schweregrad: {{ breach_severity }}.
  {{ breach_count }} Indikator(en) erkannt. Bitte sofort pruefen.
</div>
{% elif breach_severity == 'MEDIUM' %}
<div class="alert alert-warning">
  <strong>Hinweis:</strong> {{ breach_count }} auffaellige(r) Indikator(en) erkannt (Schweregrad: MEDIUM).
</div>
{% else %}
<div class="alert alert-success">
  Keine Datenschutzverletzungen erkannt. Letzte Pruefung: {{ checked_at }}.
</div>
{% endif %}

<div class="grid">
  <!-- Datenbestand -->
  <div class="card">
    <h3>Datenbestand</h3>
    <div class="stat-row">
      <span class="stat-label">Faelle gesamt</span>
      <span class="stat-value">{{ stats.total_cases }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Aktive Faelle</span>
      <span class="stat-value green">{{ stats.active_cases }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Anonymisierte Faelle</span>
      <span class="stat-value yellow">{{ stats.anonymized_cases }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Pseudonym-Zuordnungen</span>
      <span class="stat-value">{{ stats.pseudonym_mappings }}</span>
    </div>
  </div>

  <!-- Aufbewahrung -->
  <div class="card">
    <h3>Aufbewahrungsfristen</h3>
    <div class="stat-row">
      <span class="stat-label">Aufbewahrungsfrist</span>
      <span class="stat-value">{{ retention_days }} Tage</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Faelle ueber Frist</span>
      <span class="stat-value {% if overdue_cases > 0 %}red{% else %}green{% endif %}">{{ overdue_cases }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Naechste Auto-Bereinigung</span>
      <span class="stat-value">Manuell ausloesen</span>
    </div>
  </div>

  <!-- Einwilligungen -->
  <div class="card">
    <h3>Einwilligungen</h3>
    <div class="stat-row">
      <span class="stat-label">Einwilligungen gesamt</span>
      <span class="stat-value">{{ stats.consent_records }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Aktive Einwilligungen</span>
      <span class="stat-value green">{{ stats.active_consents }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Widerrufene Einwilligungen</span>
      <span class="stat-value yellow">{{ stats.consent_records - stats.active_consents }}</span>
    </div>
  </div>

  <!-- Breach-Status -->
  <div class="card">
    <h3>Breach-Erkennung</h3>
    <div class="stat-row">
      <span class="stat-label">Status</span>
      <span class="stat-value">
        {% if breach_severity == 'NONE' %}
          <span class="badge badge-green">Keine Auffaelligkeiten</span>
        {% elif breach_severity == 'MEDIUM' %}
          <span class="badge badge-yellow">{{ breach_severity }}</span>
        {% else %}
          <span class="badge badge-red">{{ breach_severity }}</span>
        {% endif %}
      </span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Indikatoren</span>
      <span class="stat-value">{{ breach_count }}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Pruefzeitraum</span>
      <span class="stat-value">24 Stunden</span>
    </div>
  </div>
</div>

<!-- Letzte Exporte -->
<div class="card" style="margin-bottom: 16px;">
  <h3>Letzte Datenexporte</h3>
  {% if recent_exports %}
  <table>
    <thead><tr><th>Zeitpunkt</th><th>Benutzer</th><th>Aktion</th><th>Details</th></tr></thead>
    <tbody>
    {% for e in recent_exports %}
    <tr>
      <td>{{ e.timestamp.strftime('%d.%m.%Y %H:%M') if e.timestamp else '-' }}</td>
      <td>{{ e.username or '-' }}</td>
      <td>{{ e.action }}</td>
      <td>{{ e.details or '-' }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p style="color:#8b949e; padding: 8px 0;">Keine Exporte in den letzten 30 Tagen.</p>
  {% endif %}
</div>

<!-- Aktionen -->
<div class="card">
  <h3>Aktionen</h3>
  <button class="btn btn-primary" onclick="runAction('/api/dsgvo/auto-cleanup', 'POST')">Auto-Bereinigung starten</button>
  <button class="btn btn-info" onclick="runAction('/api/dsgvo/check-breach', 'POST')">Breach-Check durchfuehren</button>
  <button class="btn btn-info" onclick="runAction('/api/dsgvo/minimization-report', 'GET')">Minimierungsbericht</button>
  <button class="btn btn-info" onclick="runAction('/api/dsgvo/export-all', 'GET')">Gesamtexport</button>
  <div id="result-box"></div>
</div>

</div>

<script>
async function runAction(url, method) {
  const box = document.getElementById('result-box');
  box.style.display = 'block';
  box.textContent = 'Wird ausgefuehrt...';
  try {
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.content || '';
    const resp = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: method === 'POST' ? '{}' : undefined,
    });
    const data = await resp.json();
    box.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    box.textContent = 'Fehler: ' + err.message;
  }
}
</script>
</body>
</html>"""


@dsgvo_bp.route("/dsgvo", methods=["GET"])
@role_required(*DSGVO_ROLES)
def dashboard():
    """DSGVO-Dashboard mit Datenschutz-Übersicht."""
    retention_days = _get_retention_days()
    cutoff = _utcnow() - timedelta(days=retention_days)

    # Statistics
    stats = {
        "total_cases": CaseDefinition.query.count(),
        "anonymized_cases": CaseDefinition.query.filter_by(patient="GELÖSCHT").count(),
        "active_cases": CaseDefinition.query.filter(CaseDefinition.patient != "GELÖSCHT").count(),
        "pseudonym_mappings": PseudonymMapping.query.count(),
        "consent_records": ConsentRecord.query.count(),
        "active_consents": ConsentRecord.query.filter(ConsentRecord.withdrawn_at.is_(None)).count(),
    }

    # Overdue cases
    overdue_cases = CaseDefinition.query.filter(
        CaseDefinition.updated_at < cutoff,
        CaseDefinition.patient != "GELÖSCHT",
    ).count()

    # Recent exports (last 30 days)
    export_since = _utcnow() - timedelta(days=30)
    recent_exports = AuditLog.query.filter(
        AuditLog.timestamp >= export_since,
        AuditLog.action.in_(["DSGVO_EXPORT", "DSGVO_EXPORT_ALL"]),
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()

    # Quick breach check
    since_24h = _utcnow() - timedelta(hours=24)
    denied_count = AuditLog.query.filter(
        AuditLog.timestamp >= since_24h,
        AuditLog.action == "ACCESS_DENIED",
    ).count()
    export_count = AuditLog.query.filter(
        AuditLog.timestamp >= since_24h,
        AuditLog.action.in_(["DSGVO_EXPORT", "DSGVO_EXPORT_ALL"]),
    ).count()

    breach_count = 0
    breach_severity = "NONE"
    if denied_count > 20:
        breach_count += 1
        breach_severity = "CRITICAL"
    elif denied_count > 5:
        breach_count += 1
        breach_severity = "HIGH"
    if export_count > 50:
        breach_count += 1
        breach_severity = "CRITICAL"
    elif export_count > 10:
        breach_count += 1
        if breach_severity not in ("CRITICAL",):
            breach_severity = "MEDIUM"

    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=current_user,
        stats=stats,
        retention_days=retention_days,
        overdue_cases=overdue_cases,
        recent_exports=recent_exports,
        breach_severity=breach_severity,
        breach_count=breach_count,
        checked_at=_utcnow().strftime("%d.%m.%Y %H:%M"),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Init-Funktion
# ═══════════════════════════════════════════════════════════════════════════

def init_dsgvo(app):
    """Registriert DSGVO-Blueprint und stellt Encryption-Key sicher."""
    # Ensure encryption key exists
    _ensure_encryption_key()

    # Register blueprint
    app.register_blueprint(dsgvo_bp)

    app.logger.info("[DSGVO] Blueprint registriert, Encryption-Key vorhanden.")
