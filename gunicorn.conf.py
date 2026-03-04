"""
gunicorn.conf.py - Production Gunicorn Configuration for OpMan-GPT.

Usage:
    gunicorn -c gunicorn.conf.py 'app:create_app()'

    Or via environment variable override:
    GUNICORN_WORKERS=4 gunicorn -c gunicorn.conf.py 'app:create_app()'

Environment Variables:
    GUNICORN_WORKERS   - Number of worker processes (default: 2 * CPU + 1)
    GUNICORN_BIND      - Bind address (default: 0.0.0.0:8000)
    GUNICORN_TIMEOUT   - Worker timeout in seconds (default: 120)
    GUNICORN_LOGLEVEL  - Log level (default: info)
    SSL_CERTFILE       - Path to SSL certificate (optional)
    SSL_KEYFILE        - Path to SSL private key (optional)
"""

import multiprocessing
import os

# ── Server Socket ─────────────────────────────────────────────────────────────

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
backlog = 2048

# ── Worker Processes ──────────────────────────────────────────────────────────

# Recommended: 2 * CPU cores + 1 (for I/O-bound Flask apps)
_default_workers = 2 * multiprocessing.cpu_count() + 1
workers = int(os.environ.get("GUNICORN_WORKERS", _default_workers))

# Worker class: sync is most compatible; gevent/eventlet for async
worker_class = "sync"

# Maximum number of pending connections per worker
worker_connections = 1000

# ── Timeouts ──────────────────────────────────────────────────────────────────

# Worker timeout: kill and restart worker after this many seconds of silence
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))

# Time to wait for graceful worker shutdown
graceful_timeout = 30

# Keep-alive connections timeout
keepalive = 5

# ── Logging ───────────────────────────────────────────────────────────────────

# Log to stdout for container environments
accesslog = "-"
errorlog = "-"

loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

# Extended access log format with timing information
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s'
)

# ── SSL Configuration ────────────────────────────────────────────────────────
# When terminating TLS at gunicorn (without nginx in front).
# In production with nginx, SSL is typically handled by nginx instead.

_ssl_certfile = os.environ.get("SSL_CERTFILE", "")
_ssl_keyfile = os.environ.get("SSL_KEYFILE", "")

if _ssl_certfile and _ssl_keyfile:
    certfile = _ssl_certfile
    keyfile = _ssl_keyfile
    # TLS 1.2+ only
    import ssl
    ssl_version = ssl.PROTOCOL_TLS_CLIENT
    ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20"

# ── Process Naming ────────────────────────────────────────────────────────────

proc_name = "opman-gpt"

# ── Security ──────────────────────────────────────────────────────────────────

# Limit request sizes to prevent abuse
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# ── Server Mechanics ─────────────────────────────────────────────────────────

# Preload application for faster worker startup and shared memory
preload_app = True

# Daemonize: False for container environments (container handles process management)
daemon = False

# Temporary file directory for worker heartbeat
tmp_upload_dir = None

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# ── Hooks ─────────────────────────────────────────────────────────────────────

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("OpMan-GPT gunicorn starting (workers=%d)", server.app.cfg.workers)


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.debug("Pre-fork: worker being spawned")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_exec(server):
    """Called just before a new master process is forked (on SIGHUP)."""
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("OpMan-GPT is ready. Listening on: %s", server.cfg.bind)


def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("Worker received INT or QUIT signal (pid: %s)", worker.pid)


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal (timeout)."""
    worker.log.warning("Worker timeout/abort (pid: %s)", worker.pid)


def child_exit(server, worker):
    """Called when a worker process exits."""
    server.log.info("Worker exited (pid: %s)", worker.pid)
