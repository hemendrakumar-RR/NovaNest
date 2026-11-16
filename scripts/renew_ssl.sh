#!/usr/bin/env bash
# ==============================================================================
# NovaNest Platform — Automated SSL Renewal & Nginx Reload Cron Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

LOG_FILE="/var/log/novanest_ssl_renewal.log"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Executing Let's Encrypt certificate renewal check..." >> "$LOG_FILE"

# Run renewal via certbot container
if docker compose -f docker-compose.production.yml run --rm --entrypoint "certbot renew --webroot -w /var/www/certbot --quiet" certbot >> "$LOG_FILE" 2>&1; then
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Certbot renewal check completed successfully." >> "$LOG_FILE"
    # Gracefully reload Nginx configuration without downtime
    docker compose -f docker-compose.production.yml exec -T frontend nginx -s reload >> "$LOG_FILE" 2>&1
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Nginx reloaded successfully." >> "$LOG_FILE"
else
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] [ERROR] Certbot renewal check encountered errors." >> "$LOG_FILE"
    exit 1
fi
