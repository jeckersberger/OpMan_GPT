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


def _ensure_cryptography():
    """Installiert cryptography automatisch falls nicht vorhanden."""
    try:
        import cryptography  # noqa: F401
        return True
    except ImportError:
        print("  'cryptography' nicht installiert – installiere automatisch ...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "cryptography"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("  cryptography erfolgreich installiert.")
            return True
        print(f"  Installation fehlgeschlagen: {result.stderr.strip()}")
        return False


def _generate_cert_python(lan_ip):
    """Generiert ein selbstsigniertes Zertifikat mit reinem Python (kein openssl nötig)."""
    if not _ensure_cryptography():
        return False
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime, ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        san_entries = [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]
        if lan_ip != "127.0.0.1":
            san_entries.append(x509.IPAddress(ipaddress.ip_address(lan_ip)))

        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "OpMan-GPT Local")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
            .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        with open(KEY, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            ))
        with open(CERT, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"  Warnung: Python-Zertifikat fehlgeschlagen: {e}")
        return False


def _generate_cert_openssl(lan_ip):
    """Generiert ein selbstsigniertes Zertifikat mit openssl CLI."""
    cnf_path = os.path.join(INSTANCE_DIR, "san.cnf")
    with open(cnf_path, "w") as f:
        f.write(f"""[req]
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
""")
    try:
        result = subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", KEY, "-out", CERT, "-days", "825", "-config", cnf_path,
        ], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ensure_cert():
    """Generiert das Zertifikat automatisch wenn es fehlt."""
    if os.path.exists(CERT) and os.path.exists(KEY):
        return True

    lan_ip = get_lan_ip()
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    print(f"Generiere SSL-Zertifikat für {lan_ip} ...")

    # Versuch 1: Python cryptography-Bibliothek (plattformunabhängig)
    if _generate_cert_python(lan_ip):
        print(f"  Zertifikat erstellt: {CERT}")
        return True

    # Versuch 2: openssl CLI (Linux/macOS)
    if _generate_cert_openssl(lan_ip):
        print(f"  Zertifikat erstellt: {CERT}")
        return True

    print("  Warnung: Zertifikat konnte nicht erstellt werden – Fallback auf HTTP")
    print("  Tipp: 'pip install cryptography' installieren für automatische Zertifikate")
    return False


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
        threaded=True,
    )
