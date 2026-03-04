"""
monitoring.py - Monitoring Blueprint for OpMan-GPT.

Provides health check and Prometheus-compatible metrics endpoints.
All monitoring endpoints are public (no authentication required)
to support external monitoring systems and load balancer probes.

Endpoints:
    GET /health   - Detailed health check with component status
    GET /metrics  - Prometheus-compatible metrics

Usage in create_app():
    from monitoring import init_monitoring
    init_monitoring(app)
"""

from __future__ import annotations

import os
import time
import threading
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, Response

monitoring_bp = Blueprint("monitoring", __name__)

# ── Metrics Storage (thread-safe) ────────────────────────────────────────────

_metrics_lock = threading.Lock()
_metrics = {
    "requests_total": 0,
    "requests_by_status": {},      # {"200": count, "404": count, ...}
    "requests_by_method": {},      # {"GET": count, "POST": count, ...}
    "request_latency_sum": 0.0,    # Total latency in seconds
    "request_latency_count": 0,    # Number of requests measured
    "errors_total": 0,             # 5xx responses
    "active_requests": 0,
    "start_time": time.time(),
}


# ── Health Check Endpoint ─────────────────────────────────────────────────────

@monitoring_bp.get("/health")
def health_check():
    """
    Detailed health check with component status.

    Returns JSON with:
        - status: "healthy", "degraded", or "unhealthy"
        - components: individual component health (database, disk, memory)
        - timestamp: current UTC time
    """
    components = {}
    overall_healthy = True

    # ── Database Check ────────────────────────────────────────────────────
    try:
        from database import check_database_connection
        from models import db
        db_status = check_database_connection(db)
        components["database"] = {
            "status": "healthy" if db_status["ok"] else "unhealthy",
            "type": db_status.get("type", "unknown"),
        }
        # Include pool stats if available
        for key in ("pool_size", "pool_checkedout", "pool_overflow", "pool_checkedin"):
            if key in db_status:
                components["database"][key] = db_status[key]
        if not db_status["ok"]:
            overall_healthy = False
            components["database"]["error"] = db_status.get("error", "Unknown error")
    except Exception as e:
        overall_healthy = False
        components["database"] = {"status": "unhealthy", "error": str(e)}

    # ── Disk Space Check ──────────────────────────────────────────────────
    try:
        import shutil
        disk = shutil.disk_usage("/")
        disk_pct = (disk.used / disk.total) * 100
        disk_status = "healthy" if disk_pct < 90 else ("degraded" if disk_pct < 95 else "unhealthy")
        components["disk"] = {
            "status": disk_status,
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "used_percent": round(disk_pct, 1),
        }
        if disk_status == "unhealthy":
            overall_healthy = False
    except Exception as e:
        components["disk"] = {"status": "unknown", "error": str(e)}

    # ── Memory Check ──────────────────────────────────────────────────────
    try:
        import resource
        mem_usage_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB -> MB
        components["memory"] = {
            "status": "healthy",
            "process_rss_mb": round(mem_usage_mb, 1),
        }
        # Try to read system memory from /proc/meminfo (Linux)
        try:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        meminfo[parts[0].rstrip(":")] = int(parts[1])
                total_mb = meminfo.get("MemTotal", 0) / 1024
                available_mb = meminfo.get("MemAvailable", 0) / 1024
                if total_mb > 0:
                    mem_pct = ((total_mb - available_mb) / total_mb) * 100
                    components["memory"]["system_total_mb"] = round(total_mb, 1)
                    components["memory"]["system_available_mb"] = round(available_mb, 1)
                    components["memory"]["system_used_percent"] = round(mem_pct, 1)
                    if mem_pct > 95:
                        components["memory"]["status"] = "unhealthy"
                        overall_healthy = False
                    elif mem_pct > 90:
                        components["memory"]["status"] = "degraded"
        except (FileNotFoundError, PermissionError):
            pass  # Not on Linux or no access
    except Exception as e:
        components["memory"] = {"status": "unknown", "error": str(e)}

    # ── Uptime ────────────────────────────────────────────────────────────
    uptime_seconds = time.time() - _metrics["start_time"]

    status = "healthy" if overall_healthy else "degraded"
    # Check if any component is unhealthy
    for comp in components.values():
        if comp.get("status") == "unhealthy":
            status = "unhealthy"
            break

    result = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime_seconds, 1),
        "components": components,
    }

    http_status = 200 if status != "unhealthy" else 503
    return jsonify(result), http_status


# ── Prometheus Metrics Endpoint ───────────────────────────────────────────────

@monitoring_bp.get("/metrics")
def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.

    Returns metrics in Prometheus text exposition format.
    """
    with _metrics_lock:
        lines = []

        # ── Request metrics ───────────────────────────────────────────────
        lines.append("# HELP opman_requests_total Total number of HTTP requests.")
        lines.append("# TYPE opman_requests_total counter")
        lines.append(f'opman_requests_total {_metrics["requests_total"]}')

        lines.append("# HELP opman_requests_by_status HTTP requests by status code.")
        lines.append("# TYPE opman_requests_by_status counter")
        for status_code, count in sorted(_metrics["requests_by_status"].items()):
            lines.append(f'opman_requests_by_status{{code="{status_code}"}} {count}')

        lines.append("# HELP opman_requests_by_method HTTP requests by method.")
        lines.append("# TYPE opman_requests_by_method counter")
        for method, count in sorted(_metrics["requests_by_method"].items()):
            lines.append(f'opman_requests_by_method{{method="{method}"}} {count}')

        # ── Latency ───────────────────────────────────────────────────────
        lines.append("# HELP opman_request_latency_seconds Total request processing time.")
        lines.append("# TYPE opman_request_latency_seconds summary")
        lines.append(f'opman_request_latency_seconds_sum {_metrics["request_latency_sum"]:.6f}')
        lines.append(f'opman_request_latency_seconds_count {_metrics["request_latency_count"]}')

        # ── Errors ────────────────────────────────────────────────────────
        lines.append("# HELP opman_errors_total Total 5xx error responses.")
        lines.append("# TYPE opman_errors_total counter")
        lines.append(f'opman_errors_total {_metrics["errors_total"]}')

        # ── Active requests ───────────────────────────────────────────────
        lines.append("# HELP opman_active_requests Current in-flight requests.")
        lines.append("# TYPE opman_active_requests gauge")
        lines.append(f'opman_active_requests {_metrics["active_requests"]}')

        # ── Uptime ────────────────────────────────────────────────────────
        uptime = time.time() - _metrics["start_time"]
        lines.append("# HELP opman_uptime_seconds Application uptime in seconds.")
        lines.append("# TYPE opman_uptime_seconds gauge")
        lines.append(f"opman_uptime_seconds {uptime:.1f}")

    # ── Database connection pool stats ────────────────────────────────────
    try:
        from models import db
        pool = db.engine.pool
        if hasattr(pool, "size"):
            lines.append("# HELP opman_db_pool_size Database connection pool size.")
            lines.append("# TYPE opman_db_pool_size gauge")
            lines.append(f"opman_db_pool_size {pool.size()}")

            lines.append("# HELP opman_db_pool_checkedout Connections currently checked out.")
            lines.append("# TYPE opman_db_pool_checkedout gauge")
            lines.append(f"opman_db_pool_checkedout {pool.checkedout()}")

            lines.append("# HELP opman_db_pool_overflow Current overflow connections.")
            lines.append("# TYPE opman_db_pool_overflow gauge")
            lines.append(f"opman_db_pool_overflow {pool.overflow()}")

            lines.append("# HELP opman_db_pool_checkedin Connections currently in pool.")
            lines.append("# TYPE opman_db_pool_checkedin gauge")
            lines.append(f"opman_db_pool_checkedin {pool.checkedin()}")
    except Exception:
        pass  # Pool stats not available (e.g., SQLite)

    # ── Active sessions ───────────────────────────────────────────────────
    try:
        from models import db, User
        active_users = User.query.filter_by(is_active_user=True, is_locked=False).count()
        lines.append("# HELP opman_active_users Number of active (non-locked) user accounts.")
        lines.append("# TYPE opman_active_users gauge")
        lines.append(f"opman_active_users {active_users}")
    except Exception:
        pass

    lines.append("")  # Trailing newline
    return Response("\n".join(lines), mimetype="text/plain; version=0.0.4; charset=utf-8")


# ── Middleware for Request Metrics ────────────────────────────────────────────

def _before_request():
    """Record request start time and increment active requests."""
    request._monitoring_start = time.time()
    with _metrics_lock:
        _metrics["active_requests"] += 1


def _after_request(response):
    """Record request metrics after each request."""
    start_time = getattr(request, "_monitoring_start", None)
    with _metrics_lock:
        _metrics["requests_total"] += 1
        _metrics["active_requests"] = max(0, _metrics["active_requests"] - 1)

        # Status code tracking
        status = str(response.status_code)
        _metrics["requests_by_status"][status] = _metrics["requests_by_status"].get(status, 0) + 1

        # Method tracking
        method = request.method
        _metrics["requests_by_method"][method] = _metrics["requests_by_method"].get(method, 0) + 1

        # Latency tracking
        if start_time is not None:
            latency = time.time() - start_time
            _metrics["request_latency_sum"] += latency
            _metrics["request_latency_count"] += 1

        # Error tracking
        if response.status_code >= 500:
            _metrics["errors_total"] += 1

    return response


def _teardown_request(exception):
    """Ensure active request count is decremented even on errors."""
    if exception:
        with _metrics_lock:
            _metrics["active_requests"] = max(0, _metrics["active_requests"] - 1)
            _metrics["errors_total"] += 1


# ── Initialization ────────────────────────────────────────────────────────────

def init_monitoring(app):
    """
    Initialize monitoring for the Flask application.

    Registers the monitoring blueprint and installs request hooks
    for automatic metrics collection.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(monitoring_bp)

    # Install request hooks for metrics collection
    app.before_request(_before_request)
    app.after_request(_after_request)
    app.teardown_request(_teardown_request)

    app.logger.info("Monitoring initialized: /health and /metrics endpoints active.")
