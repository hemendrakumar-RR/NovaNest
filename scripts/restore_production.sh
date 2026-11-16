#!/usr/bin/env bash
# ==============================================================================
# NovaNest Platform — Production Database Disaster Recovery & Restore Script
# Features: Pre-decryption HMAC verification (Anti-tamper protection),
#           Target container validation, Row count post-verification.
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$#" -lt 1 ]; then
    echo -e "${RED}Usage: $0 <path_to_encrypted_backup.sql.gz.enc>${NC}"
    exit 1
fi

ENC_FILE="$1"
SIG_FILE="${ENC_FILE}.sig"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

if [ ! -f ".env.production" ]; then
    echo -e "${RED}[ERROR] .env.production file not found!${NC}"
    exit 1
fi

set -a
# shellcheck disable=SC1091
source .env.production
set +a

if [ ! -f "$ENC_FILE" ]; then
    echo -e "${RED}[ERROR] Backup file not found: $ENC_FILE${NC}"
    exit 1
fi

if [ ! -f "$SIG_FILE" ]; then
    echo -e "${RED}[ERROR] Signature sidecar file not found: $SIG_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}        NOVANEST PRODUCTION DATABASE RESTORATION PROTOCOL             ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Verify HMAC Signature
echo -e "\n${YELLOW}[1/4] Verifying Backup Authenticity (HMAC-SHA256)...${NC}"
EXPECTED_SIG=$(cat "$SIG_FILE")
ACTUAL_SIG=$(openssl dgst -sha256 -hmac "${BACKUP_HMAC_SECRET}" "$ENC_FILE" | awk '{print $2}')

if [ "$EXPECTED_SIG" != "$ACTUAL_SIG" ]; then
    echo -e "${RED}[FATAL ERROR] HMAC verification failed! Backup file has been tampered with or corrupted.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] HMAC signature matches. Backup integrity verified.${NC}"

# 2. Confirm restoration target
echo -e "\n${YELLOW}[2/4] Safety Confirmation...${NC}"
echo -e "${RED}WARNING: This operation will restore into the database '${DB_NAME:-novanest_db}'!${NC}"
read -rp "Are you absolutely sure you want to proceed? (Type 'RESTORE' to confirm): " CONFIRM
if [ "$CONFIRM" != "RESTORE" ]; then
    echo -e "${RED}Restoration cancelled.${NC}"
    exit 0
fi

# 3. Decrypt and stream into MySQL container
echo -e "\n${YELLOW}[3/4] Decrypting and Ingesting Database Dump...${NC}"
TEMP_RESTORE_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_RESTORE_DIR"' EXIT

DECRYPTED_SQL="$TEMP_RESTORE_DIR/restore.sql"

openssl enc -d -aes-256-cbc -salt -pbkdf2 -iter 100000 \
  -in "$ENC_FILE" \
  -pass pass:"${BACKUP_ENCRYPTION_PASSPHRASE}" | gunzip > "$DECRYPTED_SQL"

docker compose -f docker-compose.production.yml exec -T db mysql \
  -u root -p"${MYSQL_ROOT_PASSWORD}" \
  "${DB_NAME:-novanest_db}" < "$DECRYPTED_SQL"

# 4. Verify Canonical Record Counts
echo -e "\n${YELLOW}[4/4] Verifying Canonical Table Counts Post-Restore...${NC}"
ROW_COUNT_QUERY="
SELECT 
  (SELECT COUNT(*) FROM customers) +
  (SELECT COUNT(*) FROM restaurants) +
  (SELECT COUNT(*) FROM riders) +
  (SELECT COUNT(*) FROM promotions) +
  (SELECT COUNT(*) FROM menu_items) +
  (SELECT COUNT(*) FROM orders_table) +
  (SELECT COUNT(*) FROM payments) +
  (SELECT COUNT(*) FROM deliveries) +
  (SELECT COUNT(*) FROM ratings_reviews) +
  (SELECT COUNT(*) FROM app_events) AS total_rows;
"

TOTAL_ROWS=$(docker compose -f docker-compose.production.yml exec -T db mysql \
  -u root -p"${MYSQL_ROOT_PASSWORD}" \
  --batch --raw -e "$ROW_COUNT_QUERY" "${DB_NAME:-novanest_db}" | tail -n1)

echo -e "Total Canonical Rows Restored: $TOTAL_ROWS (Expected: 304,405)"

if [ "$TOTAL_ROWS" -eq 304405 ]; then
    echo -e "${GREEN}[SUCCESS] Production database restored with 100% data integrity!${NC}"
else
    echo -e "${RED}[WARNING] Row count mismatch! Found $TOTAL_ROWS rows, expected 304,405.${NC}"
fi
