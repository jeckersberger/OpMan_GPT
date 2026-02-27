"""
Startet OpMan-GPT mit HTTPS (selbstsigniertes Zertifikat).
Erforderlich für GPS-Standortübertragung auf mobilen Geräten.

Aufruf:
    python run.py

Das Zertifikat gilt für:
    https://21.0.0.204:5000  (LAN)
    https://localhost:5000

Beim ersten Aufruf im Browser muss das Zertifikat als Ausnahme
akzeptiert werden (einmalige Sicherheitswarnung).
"""

import os
from app import create_app

CERT = os.path.join(os.path.dirname(__file__), "instance", "cert.pem")
KEY  = os.path.join(os.path.dirname(__file__), "instance", "key.pem")

if not os.path.exists(CERT) or not os.path.exists(KEY):
    print("FEHLER: Zertifikat nicht gefunden.")
    print("  Führe zuerst 'python gen_cert.py' aus.")
    raise SystemExit(1)

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  OpMan-GPT startet mit HTTPS")
    print(f"  https://21.0.0.204:5000      ← LAN (Handy)")
    print(f"  https://localhost:5000        ← lokal")
    print("  Beim ersten Öffnen: Sicherheitswarnung → 'Trotzdem öffnen'")
    print("=" * 60)
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        ssl_context=(CERT, KEY),
    )
