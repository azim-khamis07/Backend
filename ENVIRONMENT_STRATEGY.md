# Environment Strategy & Best Practices

**Version:** 2.0  
**Last Updated:** 2026-01-08

---

## Environment Overview

We use a **three-tier environment strategy** following industry best practices:

```
┌─────────────┐
│   Feature   │
│   Branch    │
└──────┬──────┘
       │
       v
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│     DEV     │ ───> │   STAGING   │ ───> │ PRODUCTION  │
│  (develop)  │      │  (develop)  │      │   (main)    │
└─────────────┘      └─────────────┘      └─────────────┘
```

---

## Environment Details

### Development (dev)

**Purpose**: Active development and feature testing

**Branch**: `develop`

**Characteristics**:
- Cost-optimized infrastructure
- Single instance deployment
- No NAT Gateway (saves ~$35/month)
- Smaller database (db.t3.micro)
- Faster iteration cycles

**Deployment**:
- Automatic on push to `develop`
- Manual via workflow dispatch

**Access**:
- Developers have full access
- Can be destroyed/recreated easily
- Used for integration testing

### Staging (staging)

**Purpose**: Pre-production testing and QA

**Branch**: `develop` or manual

**Characteristics**:
- Production-like infrastructure
- Multiple instances (2 tasks)
- Full networking setup
- Medium database (db.t3.small)
- Mirrors production closely

**Deployment**:
- Manual via workflow dispatch
- Optional: Auto-deploy on `develop` merge

**Access**:
- QA team access
- Stakeholder demos
- Performance testing
- Security testing

### Production (production)

**Purpose**: Live production environment

**Branch**: `main`

**Characteristics**:
- Full-scale infrastructure
- High availability (multi-AZ)
- Production-grade security
- Full monitoring and alerting
- Backup and disaster recovery

**Deployment**:
- Automatic on push to `main`
- Manual via workflow dispatch (with approval)

**Access**:
- Restricted access
- Change management required
- Full audit logging

---

## Deployment Workflow

### Standard Flow

```
1. Developer creates feature branch
   └─> Develops feature locally

2. Push to feature branch
   └─> CI runs (tests, lint, security)

3. Create Pull Request
   └─> CI validates PR

4. Merge to develop
   └─> Auto-deploy to DEV
   └─> Test in DEV environment

5. Merge to main
   └─> Auto-deploy to PRODUCTION
   └─> Monitor production deployment
```

### Promotion Flow

```
DEV (develop branch)
  ↓ [Test & Validate]
STAGING (optional)
  ↓ [QA & Stakeholder Approval]
PRODUCTION (main branch)
```

---

## Infrastructure Comparison

| Component | Dev | Staging | Production |
|-----------|-----|---------|------------|
| **VPC CIDR** | 10.1.0.0/16 | 10.2.0.0/16 | 10.0.0.0/16 |
| **RDS Instance** | db.t3.micro | db.t3.small | db.t3.small |
| **RDS Multi-AZ** | ❌ | ❌ | ✅ (optional) |
| **Redis Node** | cache.t3.micro | cache.t3.small | cache.t3.small |
| **ECS CPU** | 512 (0.5 vCPU) | 1024 (1 vCPU) | 1024 (1 vCPU) |
| **ECS Memory** | 1024 MB (1 GB) | 2048 MB (2 GB) | 2048 MB (2 GB) |
| **ECS Tasks** | 1 | 2 | 2+ |
| **NAT Gateway** | ❌ | ✅ | ✅ |
| **Monthly Cost** | ~$51 | ~$130 | ~$130 |

---

## Branch Strategy

### Branch Naming

```
main          → Production deployments
develop       → Development deployments
feature/*     → Feature development
hotfix/*      → Production hotfixes
release/*     → Release preparation
```

### Deployment Mapping

| Branch | Environment | Trigger |
|--------|-------------|---------|
| `main` | production | Automatic on push |
| `develop` | dev | Automatic on push |
| Any | Any | Manual via workflow dispatch |

---

## Secret Management

### Per-Environment Secrets

Each environment has its own secrets:

**Development**:
- `DATABASE_URL_DEV`
- `REDIS_URL_DEV`
- `SECRET_KEY_DEV`

**Staging**:
- `DATABASE_URL_STAGING`
- `REDIS_URL_STAGING`
- `SECRET_KEY_STAGING`

**Production**:
- `DATABASE_URL_PRODUCTION`
- `REDIS_URL_PRODUCTION`
- `SECRET_KEY_PRODUCTION`

### GitHub Environments

Use GitHub Environments feature:

1. **Settings** → **Environments**
2. Create: `dev`, `staging`, `production`
3. Add environment-specific secrets
4. Set protection rules (e.g., require approval for production)

---

## Cost Optimization

### Development Environment

**Savings**:
- No NAT Gateway: **~$35/month**
- Smaller instances: **~$20/month**
- Single task: **~$15/month**

**Total Savings**: ~$70/month vs production

### Staging Environment

**Optimizations**:
- Single-AZ database (vs Multi-AZ)
- 2 tasks (vs 4+ in production)
- Standard monitoring (vs enhanced)

---

## Monitoring Strategy

### Development

- Basic CloudWatch logs
- Error tracking (optional)
- Cost alerts

### Staging

- Full CloudWatch metrics
- Error tracking enabled
- Performance monitoring
- Cost tracking

### Production

- Comprehensive monitoring
- Real-time alerts
- Performance dashboards
- Cost optimization alerts
- Security monitoring

---

## Disaster Recovery

### Backup Strategy

| Environment | Backup Frequency | Retention |
|------------|------------------|-----------|
| Dev | Daily (optional) | 7 days |
| Staging | Daily | 30 days |
| Production | Continuous | 90 days |

### Recovery Procedures

**Dev**: Recreate from scratch (fast, low cost)  
**Staging**: Restore from backup (test recovery)  
**Production**: Full disaster recovery plan

---

## Security Considerations

### Development

- Basic security
- Developer access
- Test data allowed

### Staging

- Production-like security
- Limited access
- Anonymized data

### Production

- Full security hardening
- Restricted access
- Audit logging
- Compliance requirements

---

## Best Practices Summary

1. ✅ **Always test in dev first**
2. ✅ **Use staging for final validation**
3. ✅ **Promote through environments**
4. ✅ **Never skip staging for critical changes**
5. ✅ **Monitor each environment separately**
6. ✅ **Use environment-specific secrets**
7. ✅ **Track costs per environment**
8. ✅ **Document environment-specific procedures**

---

**Last Updated**: 2026-01-08

