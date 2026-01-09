# Architecture Documentation

## Overview

The Expense Tracker Backend is built as a **modular monolith** using FastAPI, following a layered architecture pattern. This document describes the system architecture, design decisions, and implementation details.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
│              (Web, Mobile, API Consumers)                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS/REST
                       v
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Auth       │  │ Transactions │  │  Analytics   │  │
│  │   Users      │  │  Categories  │  │   Reports    │  │
│  │   Receipts   │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────┬───────────────┬───────────────┬──────────────┘
           │               │               │
           v               v               v
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │PostgreSQL│    │  Redis   │    │   S3     │
    │          │    │  Cache   │    │  Storage │
    └──────────┘    └──────────┘    └──────────┘
           │               │
           v               v
    ┌──────────────────────────┐
    │    Celery Workers         │
    │  (PDF Generation, etc.)    │
    └──────────────────────────┘
```

## Application Architecture

### Modular Monolith Pattern

The application is organized as a modular monolith, where each feature is a self-contained module:

```
app/
├── core/              # Shared core functionality
├── db/                # Database configuration
├── infra/              # Infrastructure services
├── models/             # SQLAlchemy models
├── modules/            # Feature modules
│   ├── auth/
│   ├── users/
│   ├── categories/
│   ├── transactions/
│   ├── receipts/
│   ├── reports/
│   └── analytics/
└── utils/              # Utility functions
```

### Layered Architecture

Each module follows a layered architecture:

```
┌─────────────────────────────────┐
│      Router Layer               │  FastAPI route handlers
│  (HTTP request/response)        │
└──────────────┬──────────────────┘
               │
               v
┌─────────────────────────────────┐
│      Service Layer               │  Business logic
│  (Validation, orchestration)     │
└──────────────┬──────────────────┘
               │
               v
┌─────────────────────────────────┐
│    Repository Layer              │  Database operations
│  (Data access, queries)          │
└──────────────┬──────────────────┘
               │
               v
┌─────────────────────────────────┐
│      Model Layer                 │  SQLAlchemy models
│  (Data structures)               │
└─────────────────────────────────┘
```

## Design Patterns

### 1. Repository Pattern

Each module has a repository class that encapsulates database operations:

```python
class TransactionRepository:
    def get_by_id(self, transaction_id: int, user_id: int) -> Optional[Transaction]:
        # Database query logic
```

**Benefits:**
- Separation of concerns
- Easier testing (mock repositories)
- Database-agnostic business logic

### 2. Service Pattern

Services contain business logic and orchestrate repository calls:

```python
class TransactionService:
    def create_transaction(self, user_id: int, data: dict) -> dict:
        # Validation
        # Business rules
        # Repository calls
```

**Benefits:**
- Centralized business logic
- Transaction management
- Validation and authorization

### 3. Dependency Injection

FastAPI's dependency injection is used throughout:

```python
def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    repo = TransactionRepository(db)
    return TransactionService(repo)
```

## Data Flow

### Request Flow

1. **Client Request** → FastAPI Router
2. **Router** → Validates request (Pydantic schemas)
3. **Router** → Calls Service
4. **Service** → Validates business rules
5. **Service** → Calls Repository
6. **Repository** → Executes database query
7. **Response** flows back through layers

### Example: Create Transaction

```
POST /api/v1/transactions
  ↓
TransactionRouter.create_transaction()
  ↓
TransactionService.create_transaction()
  ↓ (validate category ownership)
  ↓ (validate date rules)
  ↓
TransactionRepository.create()
  ↓
Database INSERT
  ↓
Return TransactionResponse
```

## Database Design

### Schema Overview

```
users
  ├── id (PK)
  ├── email (unique)
  ├── password_hash
  └── timestamps

categories
  ├── id (PK)
  ├── user_id (FK → users)
  ├── name
  ├── type (expense/income)
  └── timestamps

transactions
  ├── id (PK)
  ├── user_id (FK → users)
  ├── category_id (FK → categories)
  ├── amount
  ├── type (expense/income)
  ├── occurred_at
  └── timestamps

receipts
  ├── id (PK)
  ├── transaction_id (FK → transactions, unique)
  ├── s3_key
  ├── content_type
  └── size

report_jobs
  ├── id (PK)
  ├── user_id (FK → users)
  ├── params_json
  ├── status
  ├── s3_key
  └── timestamps
```

### Indexes

Key indexes for performance:

- `users.email` (unique)
- `categories(user_id, name)` (unique per user)
- `transactions(user_id, occurred_at DESC)`
- `transactions(user_id, category_id)`
- `report_jobs(user_id, status)`

## Caching Strategy

### Redis Caching

**Cache Keys:**
- `dash:{user_id}:{year}-{month}` - Monthly summary
- `analytics:{user_id}:by-category:{start}:{end}` - Category breakdown
- `analytics:{user_id}:cashflow:{start}:{end}:{interval}` - Cashflow data

**TTL:** 30 minutes (configurable)

**Invalidation:**
- On transaction create/update/delete
- Pattern-based invalidation: `analytics:{user_id}:*`

## Background Jobs

### Celery Configuration

- **Broker**: Redis
- **Backend**: Redis
- **Queues**: Separate queue for reports
- **Retries**: 3 retries with exponential backoff

### Task Flow

```
POST /api/v1/reports/pdf
  ↓
Create ReportJob (status: pending)
  ↓
Enqueue Celery Task
  ↓
Worker picks up task
  ↓
Mark job as processing
  ↓
Generate PDF
  ↓
Upload to S3
  ↓
Mark job as completed
```

## Security

### Authentication

- **JWT Tokens**: Access tokens (30 min) + Refresh tokens (7 days)
- **Password Hashing**: bcrypt with automatic truncation for 72-byte limit
- **Token Validation**: On every protected endpoint

### Authorization

- **User Scoping**: All operations are user-scoped
- **Ownership Checks**: Verify user owns resources before operations
- **Transaction Isolation**: Users can only access their own data

### File Security

- **S3 Storage**: Private buckets
- **Pre-signed URLs**: Time-limited access
- **File Validation**: Type and size checks

## Performance Optimizations

### Database

- **Connection Pooling**: SQLAlchemy connection pool
- **Eager Loading**: `joinedload` for relationships
- **Cursor Pagination**: Efficient for large datasets
- **Indexes**: Strategic indexes on frequently queried columns

### Caching

- **Aggregate Caching**: Cache expensive aggregation queries
- **Smart Invalidation**: Pattern-based cache clearing
- **TTL Management**: Balance freshness vs performance

### Query Optimization

- **Selective Loading**: Load only needed columns
- **Batch Operations**: Reduce database round trips
- **Query Batching**: Combine related queries

## Error Handling

### Exception Hierarchy

```
BaseAPIException
  ├── NotFoundError (404)
  ├── ValidationError (422)
  ├── AuthenticationError (401)
  ├── AuthorizationError (403)
  └── ConflictError (409)
```

### Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "message": "Error message",
    "detail": {},
    "path": "/api/v1/endpoint"
  }
}
```

## Testing Strategy

### Test Types

1. **Unit Tests**: Service and repository logic
2. **Integration Tests**: API endpoints
3. **E2E Tests**: Complete user flows

### Test Coverage

- **Target**: >80% coverage
- **Tools**: pytest, pytest-cov
- **Fixtures**: Database, Redis, authenticated clients

## Deployment

### Docker

- **Multi-stage builds**: Optimized production images
- **Health checks**: Container health monitoring
- **Environment variables**: Configuration via env vars

### CI/CD

- **GitHub Actions**: Automated testing and deployment
- **Quality Gates**: Linting, type checking, security scans
- **Coverage Reports**: Track test coverage over time

## Scalability Considerations

### Horizontal Scaling

- **Stateless API**: Can scale horizontally behind load balancer
- **Database**: Connection pooling, read replicas (future)
- **Redis**: Can use Redis Cluster for high availability
- **Celery**: Scale workers independently

### Vertical Scaling

- **Database**: Optimize queries, add indexes
- **Cache**: Increase Redis memory
- **Workers**: More Celery workers for background jobs

## Monitoring & Observability

### Logging

- **Structured Logging**: JSON format
- **Request IDs**: Track requests across services
- **Log Levels**: DEBUG, INFO, WARNING, ERROR

### Metrics (Future)

- **Prometheus**: Application metrics
- **Health Endpoints**: `/health` for monitoring
- **Performance Metrics**: Response times, error rates

## Technology Stack

- **Framework**: FastAPI 0.128.0
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0
- **Cache**: Redis 7+ with hiredis
- **Background Jobs**: Celery 5.6.2
- **File Storage**: AWS S3 (boto3)
- **PDF Generation**: ReportLab 4.4.7
- **Testing**: pytest 9.0.2
- **Code Quality**: black, isort, flake8, mypy, bandit

## Future Enhancements

1. **Read Replicas**: Database read replicas for analytics
2. **Message Queue**: RabbitMQ for more complex job patterns
3. **API Rate Limiting**: Protect against abuse
4. **GraphQL**: Alternative API interface
5. **WebSockets**: Real-time updates
6. **Microservices**: Split into services if needed

---

**Last Updated**: 2026-01-08

**Version**: 1.0.0

