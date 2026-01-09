# Database Migration Strategy

This document outlines the strategy for managing database migrations in production.

## Overview

The project uses **Alembic** for database migrations. Migrations are version-controlled and can be applied safely in production.

## Migration Workflow

### Development

1. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "description"
   ```

2. **Review Generated Migration**
   - Check `alembic/versions/` for the new migration file
   - Review SQL changes
   - Modify if needed

3. **Test Migration**
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

4. **Commit Migration**
   ```bash
   git add alembic/versions/XXXX_description.py
   git commit -m "Add migration: description"
   ```

### Production

1. **Backup Database**
   ```bash
   pg_dump -U expenseuser expensedb > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Review Migration**
   - Read migration file
   - Understand changes
   - Check for breaking changes

3. **Apply Migration**
   ```bash
   alembic upgrade head
   ```

4. **Verify**
   - Check application health
   - Verify data integrity
   - Monitor for errors

5. **Rollback (if needed)**
   ```bash
   alembic downgrade -1
   ```

## Migration Best Practices

### 1. Always Backup First

**Before any migration:**
```bash
# Full database backup
pg_dump -U expenseuser expensedb > backup_$(date +%Y%m%d).sql

# Verify backup
pg_restore --list backup_*.sql
```

### 2. Test Migrations

- Test on staging first
- Test both upgrade and downgrade
- Verify data integrity after migration

### 3. Non-Breaking Changes

**Safe to apply:**
- Adding new columns (nullable)
- Adding new tables
- Adding indexes (concurrently)
- Adding constraints (if data is valid)

**Example:**
```python
def upgrade():
    op.add_column('transactions', sa.Column('tags', sa.String(500), nullable=True))
```

### 4. Breaking Changes

**Requires careful planning:**
- Dropping columns
- Changing column types
- Adding NOT NULL constraints
- Renaming columns/tables

**Strategy:**
1. Add new column (nullable)
2. Migrate data
3. Make column NOT NULL
4. Drop old column (in separate migration)

**Example:**
```python
# Migration 1: Add new column
def upgrade():
    op.add_column('transactions', sa.Column('new_field', sa.String(100), nullable=True))

# Migration 2: Migrate data
def upgrade():
    op.execute("UPDATE transactions SET new_field = old_field")

# Migration 3: Make NOT NULL and drop old
def upgrade():
    op.alter_column('transactions', 'new_field', nullable=False)
    op.drop_column('transactions', 'old_field')
```

### 5. Large Table Migrations

For tables with millions of rows:

- Use `CONCURRENTLY` for indexes
- Use batch updates
- Consider downtime window

**Example:**
```python
def upgrade():
    # Create index concurrently (PostgreSQL)
    op.execute("CREATE INDEX CONCURRENTLY idx_transactions_user_date ON transactions(user_id, occurred_at)")
```

## Migration Commands

### Common Commands

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade one step
alembic upgrade +1

# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision>

# Show SQL for migration (without applying)
alembic upgrade head --sql
```

### Production Commands

```bash
# Dry run (show SQL)
alembic upgrade head --sql

# Apply migration
alembic upgrade head

# Verify current state
alembic current
```

## Rollback Strategy

### Automatic Rollback

If migration fails:
1. Alembic tracks applied migrations
2. Failed migration is not recorded
3. Database remains in previous state
4. Fix migration and retry

### Manual Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>

# Verify rollback
alembic current
```

## Migration Checklist

### Before Migration

- [ ] Backup database
- [ ] Review migration file
- [ ] Test on staging
- [ ] Plan downtime window (if needed)
- [ ] Notify team

### During Migration

- [ ] Stop application (if needed)
- [ ] Apply migration
- [ ] Verify migration success
- [ ] Check database integrity
- [ ] Restart application

### After Migration

- [ ] Verify application health
- [ ] Monitor error logs
- [ ] Check performance
- [ ] Verify data integrity
- [ ] Document any issues

## Emergency Procedures

### Migration Failed

1. **Don't Panic**
   - Alembic tracks state
   - Database is likely in previous state

2. **Check Status**
   ```bash
   alembic current
   ```

3. **Fix Migration**
   - Identify issue
   - Fix migration file
   - Test locally

4. **Reapply**
   ```bash
   alembic upgrade head
   ```

### Data Corruption

1. **Stop Application**
2. **Restore Backup**
   ```bash
   psql -U expenseuser expensedb < backup_YYYYMMDD.sql
   ```
3. **Investigate**
4. **Fix Migration**
5. **Reapply**

## Migration Naming

Follow this convention:
```
YYYYMMDD_HHMMSS_description.py
```

Examples:
- `20260108_120000_add_tags_to_transactions.py`
- `20260108_140000_add_indexes.py`
- `20260108_160000_rename_category_type.py`

## Zero-Downtime Migrations

### Strategy

1. **Additive Changes First**
   - Add new columns (nullable)
   - Add new tables
   - Add indexes concurrently

2. **Data Migration**
   - Migrate data in background
   - Verify data integrity

3. **Application Update**
   - Deploy new code
   - Use new columns

4. **Cleanup**
   - Remove old columns (separate migration)
   - Drop unused indexes

### Example: Adding Required Field

```python
# Migration 1: Add nullable column
def upgrade():
    op.add_column('transactions', sa.Column('new_field', sa.String(100), nullable=True))

# Application: Start using new field (with fallback)

# Migration 2: Populate data
def upgrade():
    op.execute("UPDATE transactions SET new_field = 'default' WHERE new_field IS NULL")

# Migration 3: Make NOT NULL
def upgrade():
    op.alter_column('transactions', 'new_field', nullable=False)
```

## Monitoring

### Post-Migration Checks

1. **Application Health**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Database Queries**
   ```sql
   -- Check table exists
   SELECT * FROM information_schema.tables WHERE table_name = 'new_table';

   -- Check column exists
   SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions';
   ```

3. **Data Integrity**
   ```sql
   -- Count records
   SELECT COUNT(*) FROM transactions;

   -- Check for NULLs in required fields
   SELECT COUNT(*) FROM transactions WHERE new_field IS NULL;
   ```

## Best Practices Summary

1. ✅ **Always backup before migration**
2. ✅ **Test on staging first**
3. ✅ **Review migration SQL**
4. ✅ **Use transactions when possible**
5. ✅ **Plan for rollback**
6. ✅ **Monitor after migration**
7. ✅ **Document breaking changes**
8. ✅ **Use descriptive migration names**

---

**Last Updated**: 2026-01-08

