# Documentation Guide - Expense Tracker Backend

## 🌐 Accessing API Documentation

Once the Docker containers are running, you can access the interactive API documentation:

### Swagger UI (Interactive)
**URL:** http://localhost:8000/docs

- Interactive API explorer
- Try endpoints directly from browser
- View request/response schemas
- Test authentication and endpoints

### ReDoc (Alternative)
**URL:** http://localhost:8000/redoc

- Clean, readable documentation
- Better for reading API reference
- All endpoints and schemas visible

### OpenAPI JSON Schema
**URL:** http://localhost:8000/openapi.json

- Machine-readable API specification
- Use with API clients and code generators

---

## 📚 Implementation Documentation

### Phase 1: Foundation & Core Infrastructure
**File:** `PHASE1_IMPLEMENTATION.md`

**What's Included:**
- Core infrastructure setup
- Database models
- Authentication system
- Logging and middleware
- Security utilities
- Health check endpoints

**Key Endpoints:**
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Phase 2: User Management & Categories
**File:** `PHASE2_IMPLEMENTATION.md`

**What's Included:**
- User profile management
- Password change functionality
- Category CRUD operations
- User-scoped category management

**Key Endpoints:**
- `GET /api/v1/users/me` - Get user profile
- `PUT /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/password` - Change password
- `GET /api/v1/categories` - List categories
- `POST /api/v1/categories` - Create category
- `GET /api/v1/categories/{id}` - Get category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

---

## 🐳 Docker Commands

### Start All Services
```bash
docker-compose up -d
```

### Start Specific Services
```bash
# Start database and Redis only
docker-compose up -d postgres redis

# Start API service
docker-compose up -d api
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes
```bash
docker-compose down -v
```

### Rebuild and Restart
```bash
docker-compose up -d --build
```

---

## 🗄️ Database Migrations

### Create Migration
```bash
source venv/bin/activate
alembic revision --autogenerate -m "Description"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

---

## 🧪 Testing the API

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "confirm_password": "testpassword123"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 3. Get Your Profile (with token)
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Create a Category
```bash
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Groceries",
    "type": "expense",
    "description": "Food and groceries",
    "color": "#FF5733"
  }'
```

### 5. List Categories
```bash
curl -X GET "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔍 Quick Access Links

Once containers are running:

- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Root Endpoint:** http://localhost:8000/

---

## 📋 Service Status Check

```bash
# Check container status
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check database connection
docker-compose exec postgres pg_isready -U expenseuser
```

---

## 🚀 Development Workflow

1. **Start Infrastructure**
   ```bash
   docker-compose up -d postgres redis
   ```

2. **Run Migrations** (if needed)
   ```bash
   source venv/bin/activate
   alembic upgrade head
   ```

3. **Start API** (either in Docker or locally)
   ```bash
   # In Docker
   docker-compose up -d api
   
   # Or locally
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

4. **Access Documentation**
   - Open http://localhost:8000/docs
   - Explore and test endpoints

---

## 🔐 Testing Authentication

1. **Register** → Get tokens
2. **Click "Authorize" button** in Swagger UI
3. **Enter:** `Bearer YOUR_ACCESS_TOKEN`
4. **Try protected endpoints**

---

## 📖 Additional Documentation Files

- `PROJECT_BLUEPRINT.md` - Complete project architecture and plan
- `PHASE1_IMPLEMENTATION.md` - Phase 1 implementation details
- `PHASE2_IMPLEMENTATION.md` - Phase 2 implementation details
- `DEPENDENCY_MANAGEMENT.md` - Dependency management guide
- `README.md` - Project overview

---

## 🐛 Troubleshooting

### API won't start
- Check logs: `docker-compose logs api`
- Verify database is ready: `docker-compose ps`
- Check environment variables: `.env` file

### Database connection errors
- Ensure postgres is healthy: `docker-compose ps postgres`
- Check DATABASE_URL in `.env`
- Verify migrations ran: `alembic current`

### Port already in use
- Stop existing containers: `docker-compose down`
- Or change port in `docker-compose.yml`

---

## 💡 Tips

1. **Use Swagger UI** - Easiest way to test endpoints
2. **Check Logs** - `docker-compose logs -f` for real-time logs
3. **Database Tools** - Use pgAdmin or DBeaver to inspect database
4. **Postman** - Import OpenAPI schema for API testing
5. **Keep Documentation Open** - Swagger UI updates automatically

---

**Happy Coding! 🚀**

