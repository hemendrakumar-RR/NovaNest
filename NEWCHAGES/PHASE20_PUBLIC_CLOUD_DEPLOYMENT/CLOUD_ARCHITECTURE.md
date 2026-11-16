# NovaNest — Cloud Architecture Specification
## DigitalOcean VPS Production Infrastructure Design

**Document Version**: 1.0.0  
**Target Host**: DigitalOcean Cloud Droplet (Ubuntu 24.04 LTS x64)  
**Security Tier**: Enterprise Tier 1 (Hardened Edge, Isolated Network, Encrypted Storage)  

---

## 1. System Topology & Network Isolation

The NovaNest platform employs a defense-in-depth architectural model. Only the Edge Reverse Proxy (Nginx) interfaces with the public internet. All internal application components (FastAPI backend, Streamlit dashboard, MySQL database, Prometheus metrics, and Grafana visualization) operate within an isolated, private Docker bridge network (`novanest_production_network`).

```mermaid
graph TD
    subgraph PublicInternet["Public Internet Edge"]
        USER["Browser Client (HTTPS)"]
        ADMIN["Executive / SRE (HTTPS)"]
    end

    subgraph HostFirewall["DigitalOcean VPS Firewall (UFW)"]
        PORT_SSH["Port 22 (SSH pubkey only)"]
        PORT_HTTP["Port 80 (HTTP -> 301 HTTPS)"]
        PORT_HTTPS["Port 443 (TLS Termination)"]
    end

    subgraph ReverseProxy["Edge Ingress (Nginx)"]
        NGINX["Nginx 1.25+ (TLS 1.2/1.3, HSTS, Rate Limiting)"]
    end

    subgraph InternalDockerNetwork["Private Docker Network: novanest_production_network"]
        REACT["React SPA Static (/usr/share/nginx/html)"]
        FASTAPI["FastAPI Backend (4 Uvicorn Workers on :8000)"]
        STREAMLIT["Streamlit Dashboard (:8501 via /analytics/)"]
        MYSQL[("MySQL 8.0 Engine (:3306 Internal Only)")]
        PROMETHEUS["Prometheus Scraper (:9090 Internal Only)"]
        GRAFANA["Grafana Dashboards (:3000 via /grafana/)"]
        CERTBOT["Certbot Auto-Renewal Container"]
    end

    USER --> PORT_HTTPS
    USER --> PORT_HTTP
    PORT_HTTP --> NGINX
    PORT_HTTPS --> NGINX
    NGINX --> REACT
    NGINX -->|/api/*| FASTAPI
    NGINX -->|/analytics/*| STREAMLIT
    NGINX -->|/grafana/* (Auth)| GRAFANA
    NGINX -->|/.well-known/acme-challenge/*| CERTBOT

    FASTAPI --> MYSQL
    STREAMLIT --> FASTAPI
    STREAMLIT --> MYSQL
    PROMETHEUS -->|Scrapes :8000/api/metrics| FASTAPI
    GRAFANA -->|Queries TSDB| PROMETHEUS
```

---

## 2. Service Specifications & Resource Quotas

Each container runs with explicit CPU and RAM allocations configured in `docker-compose.production.yml` to prevent resource starvation, memory leaks, or noisy-neighbor degradation.

| Service | Container Name | Base Image | CPU Limit | RAM Limit | RAM Reservation | Exposed Host Port |
|---|---|---|:---:|:---:|:---:|:---:|
| **Edge Ingress / React** | `novanest-production-frontend` | `nginx:alpine` | 1.00 vCPU | 512 MB | 128 MB | `80`, `443` |
| **FastAPI Backend & AI** | `novanest-production-api` | `python:3.11-slim` | 2.00 vCPU | 2048 MB | 512 MB | *None (Internal)* |
| **Streamlit Analytics** | `novanest-production-streamlit` | `python:3.11-slim` | 1.00 vCPU | 1024 MB | 256 MB | *None (Internal)* |
| **Canonical Database** | `novanest-production-db` | `mysql:8.0.46` | 2.00 vCPU | 2048 MB | 512 MB | *None (Internal)* |
| **Prometheus TSDB** | `novanest-production-prometheus` | `prom/prometheus:v2.51.0` | 0.50 vCPU | 512 MB | 128 MB | *None (Internal)* |
| **Grafana Dashboards** | `novanest-production-grafana` | `grafana/grafana:10.4.0` | 0.50 vCPU | 512 MB | 128 MB | *None (Internal)* |
| **Certbot SSL Renewer** | `novanest-production-certbot` | `certbot/certbot:latest` | 0.25 vCPU | 128 MB | 32 MB | *None (Internal)* |
| **Total Allocation** | — | — | **7.25 vCPU (Burstable)** | **6.75 GB** | **1.68 GB** | `80`, `443` |

---

## 3. Recommended DigitalOcean Droplet Sizing Matrix

Based on runtime profiling of the multi-agent AI system, MySQL buffer pool requirements (1 GB dedicated), FastAPI Uvicorn workers, and Prometheus metrics retention:

### Tier 1: Recommended Production Droplet (Optimal Performance & Headroom)
- **Droplet Type**: DigitalOcean Premium Intel or AMD Droplet
- **Configuration**: **4 vCPUs / 8 GB RAM / 160 GB NVMe SSD / 5 TB Transfer**
- **Monthly Cost**: **$48.00 / month** (or $0.071 / hour)
- **Suitability**: Full enterprise production load. Accommodates 100+ concurrent executive queries, multi-agent AI simulations, full Prometheus TSDB retention (30 days), and background automated backups without CPU throttling.

### Tier 2: Cost-Effective Starter Droplet (Budget-Conscious Development / Pilot)
- **Droplet Type**: DigitalOcean Regular Droplet
- **Configuration**: **2 vCPUs / 4 GB RAM / 80 GB SSD / 4 TB Transfer**
- **Monthly Cost**: **$24.00 / month** (or $0.036 / hour)
- **Suitability**: Low-concurrency pilot testing. Requires tuning MySQL buffer pool to 512MB and reducing Prometheus retention to 7 days.

---

## 4. Persistent Volume Management

All stateful data is anchored to Docker named volumes backed by host NVMe filesystem storage:

1. `novanest_production_mysql_volume`: Stores the MySQL data directory `/var/lib/mysql`. Holds the canonical 304,405 records and transactional tables.
2. `novanest_production_ssl_certs_volume`: Stores Let's Encrypt certificates in `/etc/letsencrypt/live/`. Persists across container rebuilds.
3. `novanest_production_certbot_www_volume`: Serves the HTTP-01 webroot challenge tokens in `/var/www/certbot`.
4. `novanest_production_prometheus_volume`: Persists time-series metrics in `/prometheus` for 30 days.
5. `novanest_production_grafana_volume`: Stores Grafana user configurations, session data, and custom dashboard state in `/var/lib/grafana`.
