# Server Status & Quick Start

## ✅ Current Status

**PostgreSQL:** ✅ Running (healthy)  
**Redis:** ✅ Running  
**FastAPI Server:** Ready to start

---

## 🚀 Start the Server

### Option 1: Using the start script (Recommended)

```bash
./start_server.sh
```

This will:
1. ✅ Check virtual environment
2. ✅ Start PostgreSQL/Redis if needed
3. ✅ Initialize database tables
4. ✅ Start FastAPI server with auto-reload
5. ✅ Display documentation URLs

**Note:** This runs in the foreground. Press `Ctrl+C` to stop.

### Option 2: Run manually

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Ensure PostgreSQL and Redis are running
docker-compose up -d postgres redis

# 3. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Run in background

```bash
# Start in background
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/fastapi.log 2>&1 &

# Check if running
curl http://localhost:8000/health

# View logs
tail -f /tmp/fastapi.log

# Stop server
pkill -f "uvicorn.*app.main"
```

---

## 📖 Access Documentation

Once the server is running, open in your browser:

### 🎯 Swagger UI (Interactive)
**URL:** http://localhost:8000/docs

**Features:**
- ✅ Try all endpoints directly
- ✅ Test authentication (click "Authorize" button)
- ✅ View request/response schemas
- ✅ See all 16 endpoints from Phase 1, 2, and 3

### 📄 ReDoc (Readable)
**URL:** http://localhost:8000/redoc

**Features:**
- Clean, readable documentation
- All endpoints and schemas

### 📊 OpenAPI JSON
**URL:** http://localhost:8000/openapi.json

- Machine-readable API specification

---

## 🔍 Verify Server is Running

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Check if port is in use
lsof -i :8000
```

---

## 🛠️ Troubleshooting

### Port 8000 already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Database connection error

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Start PostgreSQL if needed
docker-compose up -d postgres redis

# Check database logs
docker-compose logs postgres
```

### Import errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify dependencies are installed
pip list | grep fastapi
```

---

## 📋 Available Endpoints (All Phases)

### Phase 1: Foundation
- `GET /` - Root endpoint
- `GET /health` - Health check

### Phase 1 & 2: Authentication & Users
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/users/me` - Get profile
- `PUT /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/password` - Change password

### Phase 2: Categories
- `GET /api/v1/categories` - List categories
- `GET /api/v1/categories/{id}` - Get category
- `POST /api/v1/categories` - Create category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

### Phase 3: Transactions ✨ NEW
- `GET /api/v1/transactions` - List transactions (with filters & pagination)
- `GET /api/v1/transactions/{id}` - Get transaction
- `POST /api/v1/transactions` - Create transaction
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction

**Total: 16 endpoints**

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
       "password": "testpass123",
       "confirm_password": "testpass123"
     }
     ```
   - Click "Execute"
   - Copy the `access_token`

3. **Authorize:**
   - Click the green "Authorize" button at top
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

4. **Test Transactions:**
   - `POST /api/v1/transactions` - Create a transaction
   - `GET /api/v1/transactions` - List transactions
   - `GET /api/v1/transactions/{id}` - Get transaction
   - Try filters: `?type=expense&start_date=2026-01-01`

---

## ✅ Next Steps

1. Start the server: `./start_server.sh`
2. Open Swagger UI: http://localhost:8000/docs
3. Test all endpoints
4. Read implementation docs:
   - `PHASE1_IMPLEMENTATION.md`
   - `PHASE2_IMPLEMENTATION.md`
   - `PHASE3_IMPLEMENTATION.md` ✨ NEW

---

**Ready to explore! 🚀**

