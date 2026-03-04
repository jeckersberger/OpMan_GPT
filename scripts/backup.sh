#!/usr/bin/env bash
# =============================================================================
# OpMan-GPT Backup Script
# =============================================================================
# Automated backup for SQLite and PostgreSQL databases.
# Features:
#   - Auto-detection of database type from environment
#   - AES-256-CBC encryption of backups via openssl
#   - Configurable retention (default: 30 days)
#   - Backup verification (restore test to temp DB)
#   - Offsite backup via rsync/scp (placeholder)
#   - Logging to /var/log/opman_backup.log
#
# Cron Job Setup:
#   # Daily backup at 02:00 AM
#   0 2 * * * /path/to/OpMan_GPT/scripts/backup.sh >> /var/log/opman_backup.log 2>&1
#
#   # Weekly full backup on Sunday at 03:00 AM
#   0 3 * * 0 BACKUP_TYPE=full /path/to/OpMan_GPT/scripts/backup.sh >> /var/log/opman_backup.log 2>&1
#
# Environment Variables:
#   DB_TYPE            - "sqlite" or "postgresql" (default: sqlite)
#   DB_HOST            - PostgreSQL host (default: localhost)
#   DB_PORT            - PostgreSQL port (default: 5432)
#   DB_NAME            - PostgreSQL database name (default: opman)
#   DB_USER            - PostgreSQL user (default: opman)
#   DB_PASSWORD        - PostgreSQL password
#   BACKUP_DIR         - Backup destination directory (default: /var/backups/opman)
#   BACKUP_ENCRYPTION_KEY - AES-256 encryption passphrase (REQUIRED)
#   BACKUP_RETENTION_DAYS - Days to keep backups (default: 30)
#   BACKUP_VERIFY      - Verify backup integrity (default: true)
#   SQLITE_DB_PATH     - Path to SQLite DB (default: instance/einsatzleiter.db)
#   OFFSITE_TARGET     - rsync/scp target (e.g., user@backup-server:/backups/)
#   OFFSITE_SSH_KEY    - SSH key for offsite backup
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

DB_TYPE="${DB_TYPE:-sqlite}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-opman}"
DB_USER="${DB_USER:-opman}"
DB_PASSWORD="${DB_PASSWORD:-}"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/opman}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_VERIFY="${BACKUP_VERIFY:-true}"
SQLITE_DB_PATH="${SQLITE_DB_PATH:-instance/einsatzleiter.db}"
OFFSITE_TARGET="${OFFSITE_TARGET:-}"
OFFSITE_SSH_KEY="${OFFSITE_SSH_KEY:-}"

LOG_FILE="/var/log/opman_backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="opman_${DB_TYPE}_${TIMESTAMP}"

# ── Logging ──────────────────────────────────────────────────────────────────

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}" 2>/dev/null || \
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    log "ERROR: $1" >&2
}

# ── Pre-flight Checks ───────────────────────────────────────────────────────

preflight() {
    if [ -z "${BACKUP_ENCRYPTION_KEY}" ]; then
        log_error "BACKUP_ENCRYPTION_KEY is not set. Cannot create encrypted backup."
        exit 1
    fi

    mkdir -p "${BACKUP_DIR}"

    if [ "${DB_TYPE}" = "postgresql" ]; then
        if ! command -v pg_dump &>/dev/null; then
            log_error "pg_dump not found. Install postgresql-client."
            exit 1
        fi
    fi

    if ! command -v openssl &>/dev/null; then
        log_error "openssl not found. Required for backup encryption."
        exit 1
    fi

    log "Pre-flight checks passed. DB_TYPE=${DB_TYPE}"
}

# ── SQLite Backup ────────────────────────────────────────────────────────────

backup_sqlite() {
    local src_db="${SQLITE_DB_PATH}"
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.db"
    local encrypted_file="${backup_file}.enc"

    if [ ! -f "${src_db}" ]; then
        log_error "SQLite database not found: ${src_db}"
        exit 1
    fi

    log "Starting SQLite backup: ${src_db}"

    # Use sqlite3 .backup for a consistent snapshot (handles WAL mode)
    if command -v sqlite3 &>/dev/null; then
        sqlite3 "${src_db}" ".backup '${backup_file}'"
    else
        # Fallback: file copy (less safe if writes are happening)
        cp "${src_db}" "${backup_file}"
        # Also copy WAL and SHM files if they exist
        [ -f "${src_db}-wal" ] && cp "${src_db}-wal" "${backup_file}-wal"
        [ -f "${src_db}-shm" ] && cp "${src_db}-shm" "${backup_file}-shm"
    fi

    log "SQLite backup created: ${backup_file}"

    # Encrypt
    encrypt_backup "${backup_file}" "${encrypted_file}"

    # Remove unencrypted backup
    rm -f "${backup_file}" "${backup_file}-wal" "${backup_file}-shm"

    # Verify
    if [ "${BACKUP_VERIFY}" = "true" ]; then
        verify_sqlite_backup "${encrypted_file}"
    fi

    echo "${encrypted_file}"
}

# ── PostgreSQL Backup ────────────────────────────────────────────────────────

backup_postgresql() {
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
    local encrypted_file="${backup_file}.enc"

    log "Starting PostgreSQL backup: ${DB_NAME}@${DB_HOST}:${DB_PORT}"

    export PGPASSWORD="${DB_PASSWORD}"

    pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${backup_file}" \
        2>> "${LOG_FILE}"

    unset PGPASSWORD

    local size
    size=$(du -sh "${backup_file}" 2>/dev/null | cut -f1)
    log "PostgreSQL backup created: ${backup_file} (${size})"

    # Encrypt
    encrypt_backup "${backup_file}" "${encrypted_file}"

    # Remove unencrypted backup
    rm -f "${backup_file}"

    # Verify
    if [ "${BACKUP_VERIFY}" = "true" ]; then
        verify_postgresql_backup "${encrypted_file}"
    fi

    echo "${encrypted_file}"
}

# ── Encryption ───────────────────────────────────────────────────────────────

encrypt_backup() {
    local input_file="$1"
    local output_file="$2"

    log "Encrypting backup with AES-256-CBC..."

    openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
        -in "${input_file}" \
        -out "${output_file}" \
        -pass "pass:${BACKUP_ENCRYPTION_KEY}"

    local size
    size=$(du -sh "${output_file}" 2>/dev/null | cut -f1)
    log "Encrypted backup: ${output_file} (${size})"
}

decrypt_backup() {
    local input_file="$1"
    local output_file="$2"

    openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
        -in "${input_file}" \
        -out "${output_file}" \
        -pass "pass:${BACKUP_ENCRYPTION_KEY}"
}

# ── Verification ─────────────────────────────────────────────────────────────

verify_sqlite_backup() {
    local encrypted_file="$1"
    local temp_dir
    temp_dir=$(mktemp -d)
    local temp_db="${temp_dir}/verify.db"

    log "Verifying SQLite backup..."

    # Decrypt to temp
    decrypt_backup "${encrypted_file}" "${temp_db}"

    # Run integrity check
    if command -v sqlite3 &>/dev/null; then
        local result
        result=$(sqlite3 "${temp_db}" "PRAGMA integrity_check;" 2>&1)
        if [ "${result}" = "ok" ]; then
            log "Backup verification PASSED (integrity_check: ok)"
        else
            log_error "Backup verification FAILED: ${result}"
            rm -rf "${temp_dir}"
            exit 1
        fi
    else
        log "sqlite3 not available, skipping integrity check."
    fi

    rm -rf "${temp_dir}"
}

verify_postgresql_backup() {
    local encrypted_file="$1"
    local temp_dir
    temp_dir=$(mktemp -d)
    local temp_dump="${temp_dir}/verify.sql.gz"

    log "Verifying PostgreSQL backup..."

    # Decrypt to temp
    decrypt_backup "${encrypted_file}" "${temp_dump}"

    # Verify the dump file is readable by pg_restore
    if pg_restore --list "${temp_dump}" > /dev/null 2>&1; then
        log "Backup verification PASSED (pg_restore --list succeeded)"
    else
        log_error "Backup verification FAILED (pg_restore --list returned error)"
        rm -rf "${temp_dir}"
        exit 1
    fi

    rm -rf "${temp_dir}"
}

# ── Retention ────────────────────────────────────────────────────────────────

cleanup_old_backups() {
    log "Cleaning up backups older than ${BACKUP_RETENTION_DAYS} days..."

    local count
    count=$(find "${BACKUP_DIR}" -name "opman_*.enc" -type f -mtime "+${BACKUP_RETENTION_DAYS}" | wc -l)

    if [ "${count}" -gt 0 ]; then
        find "${BACKUP_DIR}" -name "opman_*.enc" -type f -mtime "+${BACKUP_RETENTION_DAYS}" -delete
        log "Removed ${count} expired backup(s)."
    else
        log "No expired backups to remove."
    fi
}

# ── Offsite Backup ───────────────────────────────────────────────────────────

offsite_sync() {
    local backup_file="$1"

    if [ -z "${OFFSITE_TARGET}" ]; then
        log "No OFFSITE_TARGET configured. Skipping offsite sync."
        return 0
    fi

    log "Syncing backup to offsite: ${OFFSITE_TARGET}"

    local ssh_opts=""
    if [ -n "${OFFSITE_SSH_KEY}" ]; then
        ssh_opts="-e 'ssh -i ${OFFSITE_SSH_KEY} -o StrictHostKeyChecking=yes'"
    fi

    # Use rsync for efficient transfer with resume support
    if command -v rsync &>/dev/null; then
        eval rsync -avz --progress ${ssh_opts} \
            "${backup_file}" \
            "${OFFSITE_TARGET}" \
            2>> "${LOG_FILE}"
        log "Offsite sync completed via rsync."
    elif command -v scp &>/dev/null; then
        # Fallback to scp
        local scp_opts=""
        if [ -n "${OFFSITE_SSH_KEY}" ]; then
            scp_opts="-i ${OFFSITE_SSH_KEY}"
        fi
        scp ${scp_opts} "${backup_file}" "${OFFSITE_TARGET}" 2>> "${LOG_FILE}"
        log "Offsite sync completed via scp."
    else
        log_error "Neither rsync nor scp found. Cannot perform offsite sync."
        return 1
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
    log "============================================================"
    log "OpMan-GPT Backup started"
    log "============================================================"

    preflight

    local backup_file=""

    case "${DB_TYPE}" in
        sqlite)
            backup_file=$(backup_sqlite)
            ;;
        postgresql|postgres)
            backup_file=$(backup_postgresql)
            ;;
        *)
            log_error "Unknown DB_TYPE: ${DB_TYPE}. Use 'sqlite' or 'postgresql'."
            exit 1
            ;;
    esac

    # Offsite sync
    offsite_sync "${backup_file}"

    # Retention cleanup
    cleanup_old_backups

    log "Backup completed successfully: ${backup_file}"
    log "============================================================"
}

main "$@"
