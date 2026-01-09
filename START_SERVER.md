# Quick Start Guide - View Documentation

## 🚀 Start the API Server

### Option 1: Local Development (Recommended for viewing docs)

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Ensure database is running (Docker)
docker-compose up -d postgres redis

# 3. Initialize database tables (if first time)
python -c "from app.db.session import init_db; init_db()"

# 4. Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

---

## 📖 Access Documentation

Once the server is running, open your browser:

### Swagger UI (Interactive)
**URL:** http://localhost:8000/docs

- ✅ Try all endpoints directly
- ✅ Test authentication
- ✅ View request/response schemas
- ✅ See all implemented endpoints

### ReDoc (Readable)
**URL:** http://localhost:8000/redoc

- Clean, readable documentation
- All endpoints and schemas

### OpenAPI JSON
**URL:** http://localhost:8000/openapi.json

- Machine-readable API specification

---

## 🔍 Available Endpoints

### Phase 1 & 2 Implemented

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

#### User Management
- `GET /api/v1/users/me` - Get profile
- `PUT /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/password` - Change password

#### Categories
- `GET /api/v1/categories` - List categories
- `GET /api/v1/categories/{id}` - Get category
- `POST /api/v1/categories` - Create category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

#### System
- `GET /` - Root endpoint
- `GET /health` - Health check

---

## 🧪 Quick Test in Swagger UI

1. **Open** http://localhost:8000/docs
2. **Register a user:**
   - Click on `POST /api/v1/auth/register`
   - Click "Try it out"
   - Enter:
     ```json
     {
       "email": "test@example.com",
       "password": "testpassword123",
       "confirm_password": "testpassword123"
     }
     ```
   - Click "Execute"
   - Copy the `access_token` from response

3. **Authorize:**
   - Click the green "Authorize" button at top
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

4. **Try protected endpoints:**
   - `GET /api/v1/users/me` - Get your profile
   - `POST /api/v1/categories` - Create a category
   - `GET /api/v1/categories` - List your categories

---

## 📚 Implementation Documentation Files

- `PROJECT_BLUEPRINT.md` - Complete project architecture
- `PHASE1_IMPLEMENTATION.md` - Phase 1 details
- `PHASE2_IMPLEMENTATION.md` - Phase 2 details
- `DOCUMENTATION_GUIDE.md` - This file

---

## 🔧 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check logs
tail -f /tmp/fastapi.log
```

### Database connection error
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

### View all logs
```bash
# Local server logs
tail -f /tmp/fastapi.log

# Or if using docker-compose
docker-compose logs -f
```

---

## ✅ Verify Everything is Working

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Open browser
xdg-open http://localhost:8000/docs  # Linux
# or
open http://localhost:8000/docs      # macOS
```

---

**Happy Exploring! 🎉**

