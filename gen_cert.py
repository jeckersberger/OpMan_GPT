"""
Generiert ein selbstsigniertes SSL-Zertifikat für OpMan-GPT.
Ausführen wenn sich die LAN-IP ändert oder das Zertifikat abläuft.

Aufruf:
    python gen_cert.py
    python gen_cert.py 192.168.1.42   # eigene IP angeben
"""

import os
import socket
import subprocess
import sys

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
CERT = os.path.join(INSTANCE_DIR, "cert.pem")
KEY  = os.path.join(INSTANCE_DIR, "key.pem")
CNF  = os.path.join(INSTANCE_DIR, "san.cnf")


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    lan_ip = sys.argv[1] if len(sys.argv) > 1 else get_lan_ip()
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    print(f"Generiere Zertifikat für IP: {lan_ip}")

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
    with open(CNF, "w") as f:
        f.write(cnf_content)

    result = subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", KEY, "-out", CERT,
        "-days", "825",
        "-config", CNF,
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("FEHLER beim Generieren:")
        print(result.stderr)
        sys.exit(1)

    print(f"Zertifikat erstellt:")
    print(f"  {CERT}")
    print(f"  {KEY}")
    print()
    print("Jetzt starten mit:  python run.py")
    print()
    print("Im Browser beim ersten Aufruf:")
    print("  Chrome/Edge:  'Erweitert' → 'Weiter zu ...'")
    print("  Firefox:      'Risiko akzeptieren und fortfahren'")
    print("  Android:      'Weitere Informationen' → 'Unsichere Verbindung'")
    print("  iOS Safari:   'Zum Website gehen'")


if __name__ == "__main__":
    main()
