#!/usr/bin/env python3
"""Startet OpMan-GPT im EINSATZMODUS (Produktiver Betrieb).

- Login + MFA erforderlich
- Keine Patientenkarten, keine Übungspatienten
- Eigene Datenbank: einsatzleiter_live.db
- Standard-Port: 5001 (HTTPS)
"""
import os
os.environ.setdefault("APP_MODE", "einsatz")

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
    port = int(os.environ.get("PORT", 5001))
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n{'='*60}")
    print(f"  EINSATZMODUS (PRODUKTIV)")
    print(f"  https://{local_ip}:{port}")
    print(f"  Login + MFA erforderlich")
    print(f"  Standard-Admin: admin / admin")
    print(f"{'='*60}\n")
    app.run(host=host, port=port, ssl_context=(CERT, KEY), debug=False)
