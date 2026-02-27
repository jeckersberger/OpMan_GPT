"""
Startet OpMan-GPT mit HTTPS (selbstsigniertes Zertifikat).
Erforderlich für GPS-Standortübertragung auf mobilen Geräten.

Aufruf:
    python run.py          # HTTPS (generiert Cert automatisch)
    python run.py --http   # nur HTTP (kein GPS auf iOS)
"""

import os
import socket
import subprocess
import sys

from app import create_app

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
CERT = os.path.join(INSTANCE_DIR, "cert.pem")
KEY  = os.path.join(INSTANCE_DIR, "key.pem")


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def ensure_cert():
    """Generiert das Zertifikat automatisch wenn es fehlt."""
    if os.path.exists(CERT) and os.path.exists(KEY):
        return True

    lan_ip = get_lan_ip()
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    cnf_path = os.path.join(INSTANCE_DIR, "san.cnf")
    cnf_content = f"""[req]
default_bits       = 2048
prompt             = no
distinguished_name = dn
x509_extensions    = v3_req

[dn]
CN = OpMan-GPT Local

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
IP.1 = {lan_ip}
IP.2 = 127.0.0.1
DNS.1 = localhost
"""
    with open(cnf_path, "w") as f:
        f.write(cnf_content)

    print(f"Generiere SSL-Zertifikat für {lan_ip} ...")
    result = subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", KEY, "-out", CERT,
        "-days", "825",
        "-config", cnf_path,
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Warnung: openssl fehlgeschlagen – Fallback auf HTTP")
        print(f"  {result.stderr.strip()}")
        return False

    print(f"  Zertifikat erstellt: {CERT}")
    return True


app = create_app()

if __name__ == "__main__":
    http_only = "--http" in sys.argv
    lan_ip = get_lan_ip()
    port = 5000

    if http_only or not ensure_cert():
        # HTTP-Modus
        proto = "http"
        ssl_ctx = None
        print()
        print("=" * 60)
        print("  OpMan-GPT startet mit HTTP")
        print(f"  http://{lan_ip}:{port}         ← LAN (Handy)")
        print(f"  http://localhost:{port}        ← lokal")
        print()
        print("  ⚠  GPS funktioniert NICHT über HTTP auf iOS/Android!")
        print("     Starte ohne --http für HTTPS mit Auto-Zertifikat.")
        print("=" * 60)
    else:
        proto = "https"
        ssl_ctx = (CERT, KEY)
        print()
        print("=" * 60)
        print("  OpMan-GPT startet mit HTTPS")
        print(f"  https://{lan_ip}:{port}        ← LAN (Handy)")
        print(f"  https://localhost:{port}        ← lokal")
        print("  Beim ersten Öffnen: Sicherheitswarnung → 'Trotzdem öffnen'")
        print("=" * 60)

    print()
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        ssl_context=ssl_ctx,
    )
