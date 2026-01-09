# Backup Strategy

This document outlines the backup strategy for the Expense Tracker Backend.

## Overview

Regular backups are essential for data protection and disaster recovery. This strategy covers database backups, S3 backups, and configuration backups.

## Database Backups

### PostgreSQL Backup

#### Automated Daily Backups

**Using pg_dump:**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/var/backups/expense-tracker"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U expenseuser -h localhost expensedb > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### Cron Schedule

```cron
# Daily backup at 2 AM
0 2 * * * /opt/expense-tracker/scripts/backup_database.sh
```

#### Manual Backup

```bash
# Full backup
pg_dump -U expenseuser expensedb > backup_$(date +%Y%m%d).sql

# Backup specific tables
pg_dump -U expenseuser -t transactions expensedb > transactions_backup.sql

# Compressed backup
pg_dump -U expenseuser expensedb | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### Restore

```bash
# Restore from backup
psql -U expenseuser expensedb < backup_20260108.sql

# Restore compressed backup
gunzip < backup_20260108.sql.gz | psql -U expenseuser expensedb
```

### Backup Retention

- **Daily backups**: Keep for 30 days
- **Weekly backups**: Keep for 12 weeks
- **Monthly backups**: Keep for 12 months
- **Yearly backups**: Keep indefinitely

## S3 Backups

### Receipts and Reports

#### Backup Strategy

1. **Enable S3 Versioning**
   - Keep all versions of files
   - Protect against accidental deletion

2. **Cross-Region Replication**
   - Replicate to secondary region
   - Disaster recovery

3. **Lifecycle Policies**
   - Move old files to Glacier
   - Reduce storage costs

#### Backup Script

```bash
#!/bin/bash
# backup_s3.sh

BUCKET_NAME="expense-tracker-receipts"
BACKUP_BUCKET="expense-tracker-backups"
DATE=$(date +%Y%m%d)

# Sync to backup bucket
aws s3 sync s3://$BUCKET_NAME s3://$BACKUP_BUCKET/daily/$DATE/

echo "S3 backup completed: $DATE"
```

## Configuration Backups

### Environment Variables

```bash
# Backup .env file
cp .env .env.backup.$(date +%Y%m%d)

# Backup to secure location
gpg --encrypt --recipient admin@example.com .env
```

### Docker Compose

```bash
# Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d)
```

## Backup Verification

### Database Backup Verification

```bash
# Check backup integrity
pg_restore --list backup_20260108.sql | head -20

# Verify backup size
ls -lh backup_*.sql

# Test restore (on test database)
createdb expensedb_test
psql -U expenseuser expensedb_test < backup_20260108.sql
```

### S3 Backup Verification

```bash
# List backup files
aws s3 ls s3://expense-tracker-backups/daily/

# Verify file count
aws s3 ls s3://expense-tracker-backups/daily/20260108/ --recursive | wc -l
```

## Automated Backup Solution

### Using AWS RDS Automated Backups

If using AWS RDS:
- Automated daily backups
- Point-in-time recovery
- 7-day retention (configurable)

### Using Managed PostgreSQL

Most managed PostgreSQL services provide:
- Automated backups
- Point-in-time recovery
- Backup retention policies

## Disaster Recovery

### Recovery Procedures

#### 1. Database Recovery

```bash
# Stop application
systemctl stop expense-tracker-api

# Restore database
psql -U expenseuser expensedb < backup_20260108.sql

# Verify data
psql -U expenseuser expensedb -c "SELECT COUNT(*) FROM transactions;"

# Restart application
systemctl start expense-tracker-api
```

#### 2. S3 Recovery

```bash
# Restore from backup
aws s3 sync s3://expense-tracker-backups/daily/20260108/ s3://expense-tracker-receipts/
```

#### 3. Full System Recovery

1. Restore database
2. Restore S3 files
3. Restore configuration
4. Verify application
5. Test functionality

## Backup Monitoring

### Health Checks

```bash
# Check backup age
find /var/backups/expense-tracker -name "db_backup_*.sql.gz" -mtime -1

# Check backup size
du -sh /var/backups/expense-tracker/

# Verify backup script ran
grep "Backup completed" /var/log/backup.log
```

### Alerts

Set up alerts for:
- Backup failures
- Backup age > 24 hours
- Backup size anomalies
- Disk space low

## Backup Best Practices

1. ✅ **Automate backups**
2. ✅ **Test restore procedures**
3. ✅ **Store backups off-site**
4. ✅ **Encrypt sensitive backups**
5. ✅ **Monitor backup health**
6. ✅ **Document recovery procedures**
7. ✅ **Regular backup verification**
8. ✅ **Version control for configs**

## Backup Locations

### Recommended Structure

```
/var/backups/expense-tracker/
├── database/
│   ├── daily/
│   │   ├── db_backup_20260108.sql.gz
│   │   └── db_backup_20260109.sql.gz
│   ├── weekly/
│   │   └── db_backup_20260101.sql.gz
│   └── monthly/
│       └── db_backup_20251201.sql.gz
├── s3/
│   └── receipts_backup_20260108.tar.gz
└── config/
    ├── .env.backup.20260108
    └── docker-compose.yml.backup.20260108
```

## Cloud Backup Solutions

### AWS

- **RDS Automated Backups**: Built-in for RDS
- **S3 Lifecycle Policies**: Automated archival
- **AWS Backup**: Centralized backup service

### Other Providers

- **Google Cloud**: Cloud SQL backups
- **Azure**: Azure Database backups
- **DigitalOcean**: Managed database backups

---

**Last Updated**: 2026-01-08

