#!/usr/bin/env bash
# ==============================================================================
# NovaNest Platform — Automated Let's Encrypt SSL Bootstrap Script
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}          NOVANEST PLATFORM — SSL CERTIFICATE INITIALIZATION          ${NC}"
echo -e "${BLUE}======================================================================${NC}"

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

if [ -z "${DOMAIN_NAME:-}" ] || [ "$DOMAIN_NAME" = "novanest.example.com" ]; then
    echo -e "${RED}[ERROR] Please configure a valid DOMAIN_NAME in .env.production!${NC}"
    exit 1
fi

if [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
    echo -e "${RED}[ERROR] Please configure a valid LETSENCRYPT_EMAIL in .env.production!${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Target Domain: ${DOMAIN_NAME}${NC}"
echo -e "${YELLOW}Contact Email: ${LETSENCRYPT_EMAIL}${NC}"

# Verify DNS resolution
echo -e "\n${YELLOW}[1/3] Verifying Public DNS Resolution...${NC}"
SERVER_IP=$(curl -s https://api.ipify.org || curl -s https://ifconfig.me)
RESOLVED_IP=$(dig +short "$DOMAIN_NAME" | tail -n1 || true)

echo -e "Server Public IP:   $SERVER_IP"
echo -e "DNS Resolved IP:    $RESOLVED_IP"

if [ "$SERVER_IP" != "$RESOLVED_IP" ]; then
    echo -e "${RED}[DNS MISMATCH WARNING] $DOMAIN_NAME does not currently resolve to this server ($SERVER_IP).${NC}"
    echo -e "${YELLOW}Let's Encrypt HTTP-01 challenge will fail unless DNS A record points to this server IP.${NC}"
    read -rp "Do you wish to proceed anyway? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborting SSL initialization.${NC}"
        exit 1
    fi
fi

# Request certificate using certbot container
echo -e "\n${YELLOW}[2/3] Requesting Production Certificate via Certbot Webroot...${NC}"
docker compose -f docker-compose.production.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $LETSENCRYPT_EMAIL \
    -d $DOMAIN_NAME \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot

echo -e "\n${YELLOW}[3/3] Reloading Nginx with Production Certificate...${NC}"
docker compose -f docker-compose.production.yml exec frontend nginx -s reload

echo -e "\n${GREEN}[SUCCESS] SSL certificate installed and Nginx reloaded!${NC}"
echo -e "${GREEN}Verify HTTPS: https://${DOMAIN_NAME}/${NC}"
