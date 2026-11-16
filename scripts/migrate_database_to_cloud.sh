#!/usr/bin/env bash
# ==============================================================================
# NovaNest Platform — Local to Cloud Database Migration Export Script
# Extracts canonical dataset (304,405 rows) from local MySQL, validates counts,
# compresses, and encrypts for secure transfer to the production cloud VPS.
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

OUT_DIR="${PROJECT_ROOT}/backup/cloud_migration"
mkdir -p "$OUT_DIR"

EXPORT_FILE="${OUT_DIR}/novanest_canonical_cloud_migration.sql.gz"
ENC_FILE="${OUT_DIR}/novanest_canonical_cloud_migration.sql.gz.enc"
SIG_FILE="${OUT_DIR}/novanest_canonical_cloud_migration.sql.gz.enc.sig"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}       NOVANEST LOCAL-TO-CLOUD DATABASE MIGRATION EXPORTER             ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Verify Local Container is Available
echo -e "\n${YELLOW}[1/4] Verifying Local MySQL Container (novanest-db)...${NC}"
if ! docker exec novanest-db mysqladmin ping -h localhost -u root -pdev_root_secret_change_me --silent; then
    echo -e "${RED}[ERROR] Local novanest-db container is not running or healthy!${NC}"
    exit 1
fi

# 2. Check Canonical Row Counts Before Migration
echo -e "\n${YELLOW}[2/4] Auditing Canonical Row Counts Pre-Export...${NC}"
QUERY="
SELECT 
  (SELECT COUNT(*) FROM customers) as customers,
  (SELECT COUNT(*) FROM restaurants) as restaurants,
  (SELECT COUNT(*) FROM riders) as riders,
  (SELECT COUNT(*) FROM promotions) as promotions,
  (SELECT COUNT(*) FROM menu_items) as menu_items,
  (SELECT COUNT(*) FROM orders_table) as orders_table,
  (SELECT COUNT(*) FROM payments) as payments,
  (SELECT COUNT(*) FROM deliveries) as deliveries,
  (SELECT COUNT(*) FROM ratings_reviews) as ratings_reviews,
  (SELECT COUNT(*) FROM app_events) as app_events,
  (SELECT COUNT(*) FROM customers) +
  (SELECT COUNT(*) FROM restaurants) +
  (SELECT COUNT(*) FROM riders) +
  (SELECT COUNT(*) FROM promotions) +
  (SELECT COUNT(*) FROM menu_items) +
  (SELECT COUNT(*) FROM orders_table) +
  (SELECT COUNT(*) FROM payments) +
  (SELECT COUNT(*) FROM deliveries) +
  (SELECT COUNT(*) FROM ratings_reviews) +
  (SELECT COUNT(*) FROM app_events) AS total;
"

COUNTS=$(docker exec novanest-db mysql -u root -pdev_root_secret_change_me --batch --raw -e "$QUERY" novanest_db | tail -n1)
TOTAL=$(echo "$COUNTS" | awk '{print $11}')

echo -e "Audited Local Total Rows: $TOTAL (Expected: 304,405)"
if [ "$TOTAL" -ne 304405 ]; then
    echo -e "${RED}[ERROR] Local database count mismatch! Found $TOTAL rows. Aborting migration export.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Canonical counts 100% verified.${NC}"

# 3. Export Cleanmysqldump
echo -e "\n${YELLOW}[3/4] Exporting and Compressing Canonical SQL Schema & Data...${NC}"
docker exec novanest-db mysqldump \
  -u root -pdev_root_secret_change_me \
  --single-transaction \
  --quick \
  --routines \
  --triggers \
  novanest_db | gzip -9 > "$EXPORT_FILE"

FILE_SIZE=$(stat -c%s "$EXPORT_FILE" 2>/dev/null || stat -f%z "$EXPORT_FILE")
echo -e "Compressed export generated: $EXPORT_FILE ($FILE_SIZE bytes)"

# 4. Encrypt for Secure Cloud Transfer
echo -e "\n${YELLOW}[4/4] Encrypting Archive with AES-256-CBC and PBKDF2...${NC}"
PASSPHRASE=$(openssl rand -hex 32)
HMAC_KEY=$(openssl rand -hex 32)

openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
  -in "$EXPORT_FILE" \
  -out "$ENC_FILE" \
  -pass pass:"$PASSPHRASE"

openssl dgst -sha256 -hmac "$HMAC_KEY" "$ENC_FILE" | awk '{print $2}' > "$SIG_FILE"

rm -f "$EXPORT_FILE"

# Save migration transfer credentials securely in output directory
cat <<EOF > "${OUT_DIR}/MIGRATION_TRANSFER_KEY.txt"
# ==============================================================================
# NOVANEST CLOUD MIGRATION ENCRYPTED PACKAGE CREDENTIALS
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# ==============================================================================
BACKUP_ENCRYPTION_PASSPHRASE=$PASSPHRASE
BACKUP_HMAC_SECRET=$HMAC_KEY
PACKAGE_FILE=novanest_canonical_cloud_migration.sql.gz.enc
SIGNATURE_FILE=novanest_canonical_cloud_migration.sql.gz.enc.sig
TOTAL_CANONICAL_ROWS=304405
EOF

chmod 600 "${OUT_DIR}/MIGRATION_TRANSFER_KEY.txt"

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}[SUCCESS] Canonical database migration package ready for cloud transfer!${NC}"
echo -e "${GREEN}Encrypted Archive: ${ENC_FILE}${NC}"
echo -e "${GREEN}HMAC Signature:    ${SIG_FILE}${NC}"
echo -e "${GREEN}Credentials File:  ${OUT_DIR}/MIGRATION_TRANSFER_KEY.txt${NC}"
echo -e "${GREEN}======================================================================${NC}"
