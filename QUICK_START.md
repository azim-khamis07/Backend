# Quick Start - View Documentation

## ✅ Docker Containers Status

PostgreSQL and Redis are running! ✅

---

## 🚀 Start the API Server

### Easy Way (Recommended)

```bash
./start_server.sh
```

This script will:
1. ✅ Activate virtual environment
2. ✅ Start PostgreSQL/Redis if needed
3. ✅ Initialize database tables
4. ✅ Start FastAPI server
5. ✅ Show you the documentation URLs

### Manual Way

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📖 Access Documentation

Once the server is running, open in your browser:

### 🎯 Swagger UI (Best for Testing)
**URL:** http://localhost:8000/docs

**Features:**
- ✅ Try all endpoints directly
- ✅ Test authentication (click "Authorize" button)
- ✅ View request/response schemas
- ✅ See all implemented endpoints from Phase 1 & 2

### 📄 ReDoc (Best for Reading)
**URL:** http://localhost:8000/redoc

**Features:**
- Clean, readable documentation
- All endpoints and schemas

### 📊 OpenAPI JSON
**URL:** http://localhost:8000/openapi.json

- Machine-readable API specification

---

## 🧪 Quick Test in Swagger UI

### Step 1: Register a User
1. Open http://localhost:8000/docs
2. Find `POST /api/v1/auth/register`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123",
     "confirm_password": "testpassword123"
   }
   ```
5. Click "Execute"
6. Copy the `access_token` from response

### Step 2: Authorize
1. Click the green **"Authorize"** button at the top
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click "Authorize"
4. Close the dialog

### Step 3: Test Endpoints
Now you can test:
- ✅ `GET /api/v1/users/me` - Get your profile
- ✅ `POST /api/v1/categories` - Create a category
- ✅ `GET /api/v1/categories` - List categories
- ✅ All other protected endpoints

---

## 📋 Available Endpoints (Phase 1 & 2)

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### User Management
- `GET /api/v1/users/me` - Get profile
- `PUT /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/password` - Change password

### Categories
- `GET /api/v1/categories` - List categories (with filters)
- `GET /api/v1/categories/{id}` - Get category
- `POST /api/v1/categories` - Create category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

### System
- `GET /` - Root endpoint
- `GET /health` - Health check

**Total: 11 endpoints implemented**

---

## 📚 Implementation Documentation

### Phase Documentation
- **`PHASE1_IMPLEMENTATION.md`** - Phase 1: Foundation & Core Infrastructure
- **`PHASE2_IMPLEMENTATION.md`** - Phase 2: User Management & Categories
- **`PROJECT_BLUEPRINT.md`** - Complete project architecture and plan
- **`DOCUMENTATION_GUIDE.md`** - Detailed documentation guide

### Other Guides
- **`START_SERVER.md`** - Detailed server startup guide
- **`DEPENDENCY_MANAGEMENT.md`** - Dependency management guide

---

## 🔍 Verify Server is Running

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Open in browser (Linux)
xdg-open http://localhost:8000/docs

# Or manually open:
# http://localhost:8000/docs
```

---

## 🐳 Docker Services

### Current Status
```bash
docker-compose ps
```

### Start/Stop Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

---

## 🎯 Next Steps

1. **Start the server:**
   ```bash
   ./start_server.sh
   ```

2. **Open documentation:**
   - Browser: http://localhost:8000/docs

3. **Test endpoints:**
   - Register a user
   - Login
   - Create categories
   - View your profile

4. **Read implementation docs:**
   - `PHASE1_IMPLEMENTATION.md`
   - `PHASE2_IMPLEMENTATION.md`

---

**Ready to explore! 🚀**

