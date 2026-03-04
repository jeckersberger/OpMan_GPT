#!/usr/bin/env python3
"""Startet OpMan-GPT im ÜBUNGSMODUS.

- Kein Login erforderlich (Auto-Login als Übungsbenutzer)
- Patientenkarten und Übungsfälle verfügbar
- Eigene Datenbank: einsatzleiter.db
- Standard-Port: 5000 (HTTPS)
"""
import os
os.environ.setdefault("APP_MODE", "uebung")

from app import create_app

app = create_app()

if __name__ == "__main__":
    import socket
    import subprocess
    import sys

    INST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    CERT = os.path.join(INST, "cert.pem")
    KEY = os.path.join(INST, "key.pem")

    if not os.path.exists(CERT):
        os.makedirs(INST, exist_ok=True)
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", KEY, "-out", CERT,
            "-days", "365", "-nodes",
            "-subj", "/CN=localhost",
        ], check=True)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n{'='*60}")
    print(f"  ÜBUNGSMODUS")
    print(f"  https://{local_ip}:{port}")
    print(f"  Kein Login erforderlich")
    print(f"{'='*60}\n")
    app.run(host=host, port=port, ssl_context=(CERT, KEY), debug=False)
