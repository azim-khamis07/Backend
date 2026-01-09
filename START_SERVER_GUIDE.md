# 🚀 How to Start the Server

You have **TWO options** to start the FastAPI server:

---

## Option 1: Local Development (Recommended for Testing) ⭐

### Using the Start Script (Easiest)

```bash
cd /home/azim/python-projects/Backend
./start_server.sh
```

This will:
- ✅ Check virtual environment
- ✅ Start PostgreSQL & Redis (via Docker)
- ✅ Initialize database tables
- ✅ Start FastAPI server on port 8000
- ✅ Auto-clear port 8000 if in use

### Manual Local Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Ensure PostgreSQL and Redis are running
docker-compose up -d postgres redis

# 3. Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Access:** http://localhost:8000/docs

---

## Option 2: Docker Compose (Full Stack)

### Start All Services

```bash
cd /home/azim/python-projects/Backend

# First, stop any existing containers and clear port 8000
docker-compose down
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Then start all services
docker-compose up
```

### Start in Background (Detached Mode)

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f api
```

### Stop All Services

```bash
docker-compose down
```

**Access:** http://localhost:8000/docs

---

## 🔧 Fix Port 8000 Already in Use

If you get this error:
```
ERROR: Bind for 0.0.0.0:8000 failed: port is already allocated
```

### Solution 1: Stop Everything

```bash
# Stop Docker containers
docker-compose down

# Kill any local uvicorn process
pkill -9 -f "uvicorn.*app.main"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Wait a moment
sleep 2

# Now start again
./start_server.sh
# OR
docker-compose up
```

### Solution 2: Use a Different Port

Edit `docker-compose.yml` and change:
```yaml
ports:
  - "8001:8000"  # Change from "8000:8000"
```

Then access: http://localhost:8001/docs

---

## ✅ Verify Server is Running

### Check Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","database":"connected","redis":"connected"}
```

### Check if Server is Running

```bash
# Check port 8000
lsof -i :8000

# Check Docker containers
docker-compose ps

# Check local uvicorn
ps aux | grep uvicorn
```

---

## 📖 Access Documentation

Once server is running:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🎯 Quick Start (Recommended)

### For Development & Testing:

```bash
./start_server.sh
```

### For Docker Deployment:

```bash
# Stop everything first
docker-compose down
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start Docker services
docker-compose up -d

# View logs
docker-compose logs -f api
```

---

## 🔄 Troubleshooting

### Port Already in Use

```bash
# One command to fix it
docker-compose down && pkill -9 -f "uvicorn" && lsof -ti:8000 | xargs kill -9 2>/dev/null && sleep 2 && ./start_server.sh
```

### Docker Container Won't Start

```bash
# Stop and remove all containers
docker-compose down --remove-orphans

# Clear Docker volumes (⚠️ This deletes data)
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache
docker-compose up
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

---

## 📋 Summary

**Best for Development:**
```bash
./start_server.sh
```

**Best for Docker:**
```bash
docker-compose down && docker-compose up
```

Both will work! Choose based on your preference. 🚀


