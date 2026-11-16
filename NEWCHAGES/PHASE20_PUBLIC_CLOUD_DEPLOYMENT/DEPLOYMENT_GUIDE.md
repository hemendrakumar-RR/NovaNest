# NovaNest — End-to-End Cloud Deployment Runbook
## DigitalOcean VPS Production Provisioning & Handover Guide

**Document Version**: 1.0.0  
**Target OS**: Ubuntu 24.04 LTS x64  
**Target Hardware**: 4 vCPU / 8 GB RAM / 160 GB NVMe SSD (DigitalOcean Droplet)  
**Estimated Provisioning Time**: ~15–20 minutes  

---

## 1. DigitalOcean Droplet Provisioning

### Step 1.1: Create Droplet in DigitalOcean Console
1. Log in to [DigitalOcean Cloud Console](https://cloud.digitalocean.com/).
2. Click **Create** -> **Droplets**.
3. Choose Region:
   - For Indian Food Delivery platform: **Bangalore (`BLR1`)** (Lowest latency to Mumbai/Delhi/Bengaluru).
   - Alternatively: Frankfurt (`FRA1`), New York (`NYC3`), or Singapore (`SGP1`).
4. Choose Image: **Ubuntu 24.04 (LTS) x64**.
5. Choose Size:
   - Select **Basic** or **General Purpose**.
   - Pick **Regular SSD** or **Premium Intel**:
     - *Recommended*: **8 GB / 4 vCPUs / 160 GB SSD** ($48/mo).
     - *Minimum*: **4 GB / 2 vCPUs / 80 GB SSD** ($24/mo).
6. Authentication:
   - Select **SSH Key**. Add your public key (`id_ed25519.pub` or `id_rsa.pub`).
7. Additional Options: Check **Add Monitoring**.
8. Hostname: Name the droplet `novanest-production-01`.
9. Click **Create Droplet**. Note the assigned public IPv4 address (e.g. `159.203.45.67`).

---

## 2. Server Security Hardening & Firewall Setup

Connect to your new server via SSH:
```bash
ssh root@159.203.45.67
```

### Step 2.1: Update System Packages & Install Core Tools
```bash
apt-get update && apt-get upgrade -y
apt-get install -y ufw fail2ban curl git htop unzip jq net-tools
```

### Step 2.2: Configure Uncomplicated Firewall (UFW)
Enforce strict default-deny policies, allowing only SSH, HTTP, and HTTPS:
```bash
# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow operational ports
ufw allow 22/tcp comment 'SSH Management'
ufw allow 80/tcp comment 'HTTP ACME & Redirect'
ufw allow 443/tcp comment 'HTTPS Production Gateway'

# Enable firewall
ufw --force enable
ufw status verbose
```
*Result*: Port 3306 (MySQL), Port 9090 (Prometheus), and internal application ports are completely invisible to external scanners.

### Step 2.3: Configure Fail2Ban (Brute-Force SSH Defense)
```bash
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 3. Docker Engine & Compose v2 Installation

Install the official Docker Engine repository:
```bash
# Add Docker GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

---

## 4. NovaNest Deployment & Configuration

### Step 4.1: Deploy Codebase to `/opt/novanest`
```bash
mkdir -p /opt/novanest
cd /opt/novanest

# Clone repository or transfer local files via rsync/git:
# git clone <your-private-repo-url> .
```

### Step 4.2: Configure Production Environment Variables
```bash
cp .env.production.example .env.production
chmod 600 .env.production

# Edit configuration file and insert cryptographically generated secrets:
nano .env.production
```
*Generate strong secrets using*:
```bash
# Generate DB password
openssl rand -hex 32
# Generate JWT key
openssl rand -hex 64
# Generate API key
openssl rand -hex 32
```

### Step 4.3: Deploy Application Cluster
```bash
chmod +x scripts/*.sh
./scripts/deploy_production.sh
```

### Step 4.4: Initialize Let's Encrypt SSL Certificate
Ensure your DNS A record points to the server IP, then run:
```bash
./scripts/init_ssl.sh
```

### Step 4.5: Ingest Canonical Database (304,405 Rows)
```bash
# Run database restoration script
./scripts/restore_production.sh /var/backups/novanest/novanest_canonical_cloud_migration.sql.gz.enc
```

---

## 5. Production Health Verification

Verify that all services are online and responding over public HTTPS:

```bash
# Check container statuses
docker compose -f docker-compose.production.yml ps

# Test HTTPS API health probe
curl -I https://novanest.example.com/api/health
# Expected: HTTP/2 200 OK

# Test Nginx edge health probe
curl -I https://novanest.example.com/nginx-health
# Expected: HTTP/2 200 OK
```

### Access URLs:
- **Executive BI Dashboard**: `https://novanest.example.com/`
- **Streamlit Analytics Engine**: `https://novanest.example.com/analytics/`
- **FastAPI Documentation / Health**: `https://novanest.example.com/api/health`
- **Grafana SRE Telemetry**: `https://novanest.example.com/grafana/`
