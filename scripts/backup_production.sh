#!/usr/bin/env bash
# ==============================================================================
# NovaNest Platform — Production Automated Encrypted Database Backup Script
# Features: Authenticated Encrypt-then-MAC (AES-256-CBC + HMAC-SHA256),
#           Zero database downtime, Automated retention pruning.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

if [ ! -f ".env.production" ]; then
    echo "[ERROR] .env.production file not found!"
    exit 1
fi

set -a
# shellcheck disable=SC1091
source .env.production
set +a

BACKUP_DIR="${BACKUP_DIR:-/var/backups/novanest}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_NAME="novanest_canonical_prod_${TIMESTAMP}"
RAW_DUMP="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
ENC_DUMP="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz.enc"
SIG_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz.enc.sig"

mkdir -p "$BACKUP_DIR"
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting production database backup: $BACKUP_NAME"

# 1. Execute live mysqldump from production container
docker compose -f docker-compose.production.yml exec -T db mysqldump \
  -u root -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction \
  --quick \
  --routines \
  --triggers \
  "${DB_NAME:-novanest_db}" | gzip -9 > "$RAW_DUMP"

DUMP_SIZE=$(stat -c%s "$RAW_DUMP" 2>/dev/null || stat -f%z "$RAW_DUMP")
if [ "$DUMP_SIZE" -lt 10000 ]; then
    echo "[ERROR] Dump file is abnormally small ($DUMP_SIZE bytes). Backup aborted."
    rm -f "$RAW_DUMP"
    exit 1
fi

# 2. Encrypt dump using AES-256-CBC with PBKDF2
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
  -in "$RAW_DUMP" -out "$ENC_DUMP" \
  -pass pass:"${BACKUP_ENCRYPTION_PASSPHRASE}"

# Remove unencrypted dump immediately
rm -f "$RAW_DUMP"

# 3. Generate HMAC-SHA256 authenticity signature sidecar (Encrypt-then-MAC)
openssl dgst -sha256 -hmac "${BACKUP_HMAC_SECRET}" "$ENC_DUMP" | awk '{print $2}' > "$SIG_FILE"

ENC_SIZE=$(stat -c%s "$ENC_DUMP" 2>/dev/null || stat -f%z "$ENC_DUMP")
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup encrypted successfully: $ENC_DUMP ($ENC_SIZE bytes)"
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Signature generated: $SIG_FILE"

# 4. Prune archives older than retention window
find "$BACKUP_DIR" -name "novanest_canonical_prod_*.enc*" -mtime "+${RETENTION_DAYS}" -delete
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup retention pruning completed (retention: ${RETENTION_DAYS} days)."
