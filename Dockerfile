# ── Build-Stage ──────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn


# ── Runtime-Stage ─────────────────────────────────────────────────
FROM python:3.12-slim

# git wird für In-Container-Updates benötigt (/api/update)
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Non-root user (UID/GID 1000) – rootless-Docker & SELinux-kompatibel
RUN groupadd -g 1000 opman && \
    useradd  -u 1000 -g opman -m -s /sbin/nologin opman

WORKDIR /app

# Abhängigkeiten aus Builder kopieren
COPY --from=builder /install /usr/local

# App-Quellcode kopieren (ohne instance/, wird als Volume gemountet)
COPY --chown=opman:opman . .

# instance/ sicherstellen – wird im Container nur genutzt wenn kein Volume
RUN mkdir -p instance && chown opman:opman instance

# Nie als root laufen
USER 1000

EXPOSE 8000

# GUNICORN_WORKERS kann per Env überschrieben werden
CMD sh -c "exec gunicorn \
      --bind 0.0.0.0:8000 \
      --workers ${GUNICORN_WORKERS:-2} \
      --timeout 120 \
      --access-logfile - \
      'app:create_app()'"
