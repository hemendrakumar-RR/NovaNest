# NovaNest — Domain & DNS Configuration Guide
## Production DNS Architecture & Ingress Mapping

**Document Version**: 1.0.0  
**Phase**: PHASE 20 (Public Cloud Deployment)  
**Status**: SPECIFIED & READY  

---

## 1. Domain Overview & Ingress Strategies

NovaNest can be deployed using either **Unified Path-Based Routing** (Recommended) or **Subdomain-Based Routing**.

### Option A: Unified Path-Based Routing (Recommended — Simplest SSL & Zero CORS)
All services are mapped cleanly under a single apex domain or subdomain:
- Main React Executive Dashboard: `https://novanest.example.com/`
- FastAPI REST API & AI Copilot: `https://novanest.example.com/api/`
- Streamlit Multipage Analytics: `https://novanest.example.com/analytics/`
- Grafana Operations Telemetry: `https://novanest.example.com/grafana/`

*Advantages*: Requires only one single SSL certificate, eliminates cross-origin resource sharing (CORS) preflight requests, and provides a unified C-suite user experience.

### Option B: Subdomain-Based Routing
- Main Dashboard: `https://app.novanest.example.com/`
- Backend API: `https://api.novanest.example.com/`
- Streamlit Analytics: `https://analytics.novanest.example.com/`
- SRE Dashboards: `https://grafana.novanest.example.com/`

---

## 2. DNS Zone Record Configuration

Configure the following records in your authoritative DNS manager (Cloudflare, DigitalOcean DNS, Namecheap, Route 53):

| Record Type | Host / Name | Target / Value | TTL | Purpose |
|:---:|:---:|:---:|:---:|---|
| **A** | `@` (or `novanest`) | `<DROPLET_PUBLIC_IPV4>` | 300s (5 min) | Apex domain pointing to DigitalOcean VPS IP |
| **A** | `app` | `<DROPLET_PUBLIC_IPV4>` | 300s (5 min) | Subdomain for React application |
| **A** | `api` | `<DROPLET_PUBLIC_IPV4>` | 300s (5 min) | Subdomain for FastAPI gateway |
| **A** | `analytics` | `<DROPLET_PUBLIC_IPV4>` | 300s (5 min) | Subdomain for Streamlit analytics |
| **A** | `grafana` | `<DROPLET_PUBLIC_IPV4>` | 300s (5 min) | Subdomain for Grafana telemetry |
| **CNAME** | `www` | `@` | 300s (5 min) | Canonical alias redirect |
| **CAA** | `@` | `0 issue "letsencrypt.org"` | 3600s | Authorize Let's Encrypt CA to issue certs |

> [!IMPORTANT]
> **Cloudflare Proxy Note**: If using Cloudflare as your DNS manager, set the initial proxy status to **"DNS Only" (Grey Cloud)** while running `scripts/init_ssl.sh`. Once Let's Encrypt validates the certificate, you may toggle the proxy to **"Proxied" (Orange Cloud)** if desired, setting SSL/TLS encryption mode to **"Full (Strict)"**.

---

## 3. Pre-Deployment DNS Verification

Run these verification commands from your local terminal before triggering Let's Encrypt certificate acquisition:

```bash
# 1. Query the A record for the target domain
dig +short novanest.example.com

# 2. Verify authoritative name server propagation
nslookup novanest.example.com 8.8.8.8

# 3. Test HTTP reachability of the port 80 challenge endpoint
curl -I http://novanest.example.com/nginx-health
# Expected response: HTTP/1.1 200 OK (Content-Type: text/plain)
```
