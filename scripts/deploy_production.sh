#!/usr/bin/env bash
# ==============================================================================
# NovaNest Platform — Automated Public Cloud Deployment Script
# DigitalOcean VPS / Linux Cloud Server
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}       NOVANEST PLATFORM — PRODUCTION CLOUD DEPLOYMENT SCRIPT         ${NC}"
echo -e "${BLUE}======================================================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 1. Check prerequisites
echo -e "\n${YELLOW}[1/6] Verifying Host Environment & Prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker is not installed. Please install Docker Engine first.${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}[ERROR] Docker Compose v2 is not installed.${NC}"
    exit 1
fi

if [ ! -f ".env.production" ]; then
    echo -e "${RED}[ERROR] .env.production file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.production.example to .env.production and configure your production secrets.${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Docker & Docker Compose available.${NC}"

# 2. Check for default placeholder secrets
echo -e "\n${YELLOW}[2/6] Auditing Production Secrets Configuration...${NC}"
if grep -q "REPLACE_WITH_" .env.production; then
    echo -e "${RED}[SECURITY ERROR] .env.production contains unreplaced template placeholders!${NC}"
    echo -e "${RED}Refusing to deploy with unconfigured production secrets.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Zero unreplaced template placeholders detected.${NC}"

# 3. Source environment variables
set -a
# shellcheck disable=SC1091
source .env.production
set +a

# 4. Create necessary host mount directories and dummy SSL if first-time boot
echo -e "\n${YELLOW}[3/6] Preparing Storage & SSL Directories...${NC}"
mkdir -p /var/backups/novanest

# Verify or bootstrap SSL cert placeholder for initial Nginx startup
if ! docker volume inspect novanest_production_ssl_certs_volume &> /dev/null; then
    echo -e "${YELLOW}Creating SSL volume...${NC}"
    docker volume create novanest_production_ssl_certs_volume
fi

# 5. Build and deploy container cluster
echo -e "\n${YELLOW}[4/6] Building and Starting Production Container Cluster...${NC}"
docker compose -f docker-compose.production.yml pull db certbot prometheus grafana || true
docker compose -f docker-compose.production.yml build --no-cache api streamlit frontend

echo -e "\n${YELLOW}[5/6] Launching Containers in Detached Mode...${NC}"
docker compose -f docker-compose.production.yml up -d

# 6. Verify service health
echo -e "\n${YELLOW}[6/6] Awaiting Service Health Verification (up to 60s)...${NC}"
RETRIES=12
SUCCESS=false

for i in $(seq 1 $RETRIES); do
    echo -e "Health probe attempt $i/$RETRIES..."
    if docker compose -f docker-compose.production.yml ps | grep -q "unhealthy"; then
        echo -e "${YELLOW}Waiting for services to become healthy...${NC}"
        sleep 5
    elif [ "$(docker compose -f docker-compose.production.yml ps -q | wc -l)" -ge 6 ]; then
        SUCCESS=true
        break
    else
        sleep 5
    fi
done

echo -e "\n${BLUE}======================================================================${NC}"
docker compose -f docker-compose.production.yml ps
echo -e "${BLUE}======================================================================${NC}"

if [ "$SUCCESS" = true ]; then
    echo -e "\n${GREEN}[SUCCESS] NovaNest Production Platform deployed successfully!${NC}"
    echo -e "${GREEN}Main Dashboard:    https://${DOMAIN_NAME}/${NC}"
    echo -e "${GREEN}Streamlit Engine:  https://${DOMAIN_NAME}/analytics/${NC}"
    echo -e "${GREEN}REST API Gateway:  https://${DOMAIN_NAME}/api/health${NC}"
    echo -e "${GREEN}Grafana Telemetry: https://${DOMAIN_NAME}/grafana/${NC}"
else
    echo -e "\n${RED}[WARNING] One or more services took longer than expected to stabilize.${NC}"
    echo -e "${YELLOW}Run 'docker compose -f docker-compose.production.yml logs' to inspect startup logs.${NC}"
fi
