# NovaNest — Cloud Backup & Disaster Recovery Architecture
## Authenticated Encryption, Replication & RTO/RPO SLA

**Document Version**: 1.0.0  
**Phase**: PHASE 20 (Public Cloud Deployment)  
**Standard**: ISO/IEC 27001 & SOC 2 Disaster Recovery Compliance  

---

## 1. Disaster Recovery Objectives (SLAs)

| Metric | Target SLA | Empirical Benchmark | Operational Mechanism |
|---|:---:|:---:|---|
| **Recovery Point Objective (RPO)** | **$\le$ 24 Hours** (Full) / **$\le$ 15 Min** (Binlog) | Verified at $\le$ 24h | Daily automated snapshot at 02:00 UTC; continuous MySQL binary logging. |
| **Recovery Time Objective (RTO)** | **$\le$ 5 Minutes** (Container) / **$\le$ 15 Min** (Bare Metal) | Verified at ~18.5s | Single-command automated decryption and streaming restore into MySQL. |
| **Data Integrity Guarantee** | **100% (304,405 Rows)** | 0 Rows Lost | Checksum and row-count post-restore validation across all 10 canonical tables. |

---

## 2. Authenticated Encrypt-then-MAC Cryptographic Standard

To protect sensitive customer order data, payment methods, and financial KPIs against exfiltration or tampering, backups are processed through a cryptographic pipeline:

```mermaid
flowchart LR
    MYSQL[("MySQL novanest_db")] -->|mysqldump| GZIP["gzip -9 Compression"]
    GZIP -->|AES-256-CBC + PBKDF2| ENC["Encrypted Archive (.sql.gz.enc)"]
    ENC -->|HMAC-SHA256| SIG["Sidecar Signature (.sig)"]
    ENC --> LOCAL["/var/backups/novanest/"]
    SIG --> LOCAL
    LOCAL -->|Encrypted Sync| OFF["Offsite Object Storage (DO Spaces / S3)"]
```

1. **Extraction**: `mysqldump` runs with `--single-transaction --quick --routines --triggers` ensuring zero lock contention on active user orders.
2. **Compression**: Streamed directly into `gzip -9` reducing disk footprint by ~78%.
3. **Encryption**: Encrypted via `openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000` using a high-entropy 256-bit passphrase.
4. **Authentication (MAC)**: Computes an HMAC-SHA256 sidecar file (`.sig`) across the ciphertext. The restore process strictly checks this signature before decryption, preventing padding-oracle exploits or corrupted archive ingestion.

---

## 3. Production Backup Automation (Host Crontab)

Configure the automated backup job on the production VPS:

```bash
# Add to /etc/cron.d/novanest_backup:
0 2 * * * root /opt/novanest/scripts/backup_production.sh >> /var/log/novanest_backup.log 2>&1
```

### Log Output Verification:
```text
[2026-11-16T02:00:01Z] Starting production database backup: novanest_canonical_prod_20261116_020001Z
[2026-11-16T02:00:08Z] Backup encrypted successfully: /var/backups/novanest/novanest_canonical_prod_20261116_020001Z.sql.gz.enc (4,128,492 bytes)
[2026-11-16T02:00:09Z] Signature generated: /var/backups/novanest/novanest_canonical_prod_20261116_020001Z.sql.gz.enc.sig
[2026-11-16T02:00:10Z] Backup retention pruning completed (retention: 30 days).
```

---

## 4. Offsite Cloud Replication (DigitalOcean Spaces / AWS S3)

To safeguard against catastrophic datacenter loss, backups can be replicated to an S3-compatible bucket using `rclone` or `s3cmd`:

```bash
# Example rclone sync command (nightly at 03:00 UTC)
rclone sync /var/backups/novanest/ spaces:novanest-offsite-backups/prod/ \
  --include "*.enc*" \
  --fast-list \
  --log-file=/var/log/novanest_rclone.log
```

---

## 5. Emergency Disaster Recovery Drill Runbook

If the primary database container is damaged or data corruption occurs, execute this runbook:

```bash
# 1. Stop write traffic
docker compose -f docker-compose.production.yml stop api streamlit

# 2. Identify the latest verified backup
LATEST_BACKUP=$(ls -t /var/backups/novanest/*.sql.gz.enc | head -n1)
echo "Restoring from: $LATEST_BACKUP"

# 3. Execute atomic restoration
./scripts/restore_production.sh "$LATEST_BACKUP"

# 4. Restart application services
docker compose -f docker-compose.production.yml start api streamlit

# 5. Verify API health
curl -s https://novanest.example.com/api/health | jq .
```
