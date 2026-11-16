# NovaNest — Phase 20: File Changes Register
## Public Cloud Deployment Infrastructure Inventory

**Phase**: PHASE 20 (Public Cloud Deployment)  
**Lead Roles**: Principal Cloud Architect & Senior DevOps Engineer  
**Date**: 2026-11-16  

---

## 1. Newly Created Infrastructure & Configuration Files

| File Path | Component | Purpose & Description |
|---|---|---|
| `docker-compose.production.yml` | Container Orchestration | Standalone production compose file for cloud VPS: 7 services (`db`, `api`, `streamlit`, `frontend`, `certbot`, `prometheus`, `grafana`), isolated internal network, zero public database ports, resource limits, and health checks. |
| `.env.production.example` | Secrets Management | Comprehensive environment template with cryptographic guidelines for generating strong 32/64-byte hex tokens via OpenSSL. |
| `docker/nginx.production.conf` | Edge Ingress Proxy | Nginx configuration enforcing Let's Encrypt ACME webroot challenge, HTTP->HTTPS redirect, TLS 1.2/1.3, HSTS, rate limiting, SSE streaming for AI, Streamlit WebSockets, and React SPA routing. |
| `scripts/deploy_production.sh` | Deployment Automation | Shell script that validates prerequisites, audits `.env.production` for placeholders, builds images, launches containers, and performs automated health probes. |
| `scripts/init_ssl.sh` | SSL Management | Acquires initial Let's Encrypt certificate via Certbot webroot mode and reloads Nginx gracefully. |
| `scripts/renew_ssl.sh` | Automated Renewal | Crontab-ready SSL renewal script that checks expiry and executes zero-downtime Nginx reload. |
| `scripts/backup_production.sh` | Disaster Recovery | Production automated encrypted database backup script (AES-256-CBC + HMAC-SHA256 signature sidecar with retention pruning). |
| `scripts/restore_production.sh` | Disaster Recovery | Atomic restoration script that validates HMAC authenticity before decryption, ingests data into MySQL, and verifies 304,405 row counts. |
| `scripts/migrate_database_to_cloud.sh` | Database Migration | Local extraction script that validates local canonical counts, generates compressed SQL dump, and encrypts for transfer to the cloud VPS. |

---

## 2. Newly Created Governance Documentation

| File Path | Description |
|---|---|
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/PHASE_PLAN.md` | Strategic plan, target cloud architecture diagram, and operational constraints. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/IMPLEMENTATION_LOG.md` | Chronological execution log and milestone tracking. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/CLOUD_ARCHITECTURE.md` | Full cloud topology, container quotas, and DigitalOcean sizing/cost matrix. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/DOMAIN_DNS_GUIDE.md` | DNS zone configuration, A/CNAME/CAA records, and propagation commands. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/SSL_CONFIGURATION.md` | Let's Encrypt ACME architecture, Qualys A+ standards, and renewal automation. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/DATABASE_MIGRATION_GUIDE.md` | Zero-loss migration protocol, 10-table catalog, and financial reconciliation. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/DEPLOYMENT_GUIDE.md` | Complete step-by-step VPS provisioning, UFW setup, Docker install, and launch guide. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/BACKUP_AND_RECOVERY.md` | Encrypt-then-MAC backup specification, RTO/RPO targets, and drill runbooks. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/SECURITY_CHECKLIST.md` | Pre-flight security audit covering network, identity, proxy, and data layers. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/TEST_RESULTS.md` | Build verification, compose syntax check, and regression test results. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/FILE_CHANGES.md` | This file inventory register. |
| `NEWCHAGES/PHASE20_PUBLIC_CLOUD_DEPLOYMENT/PHASE_SUMMARY.md` | Executive summary, cost breakdown, remaining blockers, and go-live handover. |
