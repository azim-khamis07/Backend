# Localhost:8000/docs Troubleshooting Guide

## ✅ Current Status

Your application **IS WORKING**! Here's what I verified:

1. ✅ Docker containers are running
2. ✅ API container is listening on port 8000
3. ✅ `/docs` endpoint returns HTTP 200
4. ✅ `/openapi.json` is accessible
5. ✅ Root endpoint `/` works
6. ✅ Health endpoint `/health` works

## 🌐 How to Access

### Option 1: Browser
Open your web browser and navigate to:
```
http://localhost:8000/docs
```

### Option 2: Alternative Docs
FastAPI provides two documentation interfaces:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Troubleshooting Steps

### Step 1: Check if Containers are Running
```bash
docker-compose ps
```

You should see:
- `backend-api-1` - **Up** and port `8000:8000` mapped
- `backend-postgres-1` - **Up** and **healthy**
- `backend-redis-1` - **Up**
- `backend-worker-1` - **Up**

### Step 2: Check if Port 8000 is Accessible
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"Expense Tracker API","version":"1.0.0",...}
```

### Step 3: Check API Logs
```bash
docker-compose logs api --tail=50
```

Look for:
- `INFO:     Application startup complete.` ✅
- `INFO:     Uvicorn running on http://0.0.0.0:8000` ✅

### Step 4: Test Different Endpoints
```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# OpenAPI schema
curl http://localhost:8000/openapi.json

# Docs (should return HTML)
curl http://localhost:8000/docs
```

## 🐛 Common Issues

### Issue 1: "Connection Refused"
**Symptoms**: Browser shows "Connection refused" or "Unable to connect"

**Solutions**:
1. **Check if containers are running**:
   ```bash
   docker-compose ps
   ```

2. **Restart containers**:
   ```bash
   docker-compose restart api
   ```

3. **Check if port 8000 is in use**:
   ```bash
   # Linux/Mac
   lsof -i :8000
   # or
   ss -tuln | grep 8000
   
   # Kill process if needed
   kill -9 <PID>
   ```

4. **Rebuild and restart**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Issue 2: "This site can't be reached"
**Symptoms**: Browser shows network error

**Solutions**:
1. **Check Docker port mapping**:
   ```bash
   docker-compose ps
   ```
   Should show: `0.0.0.0:8000->8000/tcp`

2. **Try accessing from container**:
   ```bash
   docker-compose exec api curl http://localhost:8000/health
   ```

3. **Check firewall settings** (Linux):
   ```bash
   sudo ufw status
   sudo ufw allow 8000/tcp  # If needed
   ```

### Issue 3: "404 Not Found"
**Symptoms**: Browser shows 404 for `/docs`

**Solutions**:
1. **Check if app is running**:
   ```bash
   curl http://localhost:8000/
   ```

2. **Check logs for errors**:
   ```bash
   docker-compose logs api --tail=100 | grep -i error
   ```

3. **Verify route registration**:
   ```bash
   curl http://localhost:8000/openapi.json | grep -o '"\/docs"' || echo "Docs route not found"
   ```

### Issue 4: Application Keeps Reloading
**Symptoms**: Logs show constant reloading, app won't stabilize

**Solutions**:
1. **Stop file watching** (remove `--reload` flag):
   Edit `docker-compose.yml`:
   ```yaml
   command: uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Then restart:
   ```bash
   docker-compose restart api
   ```

2. **Exclude problematic files**:
   Add to `.dockerignore`:
   ```
   *.pyc
   __pycache__
   .git
   ```

3. **Check for import errors**:
   ```bash
   docker-compose exec api python -c "from app.main import app; print('OK')"
   ```

### Issue 5: Database Connection Issues
**Symptoms**: Health check shows `"database": "disconnected"`

**Solutions**:
1. **Check PostgreSQL container**:
   ```bash
   docker-compose ps postgres
   # Should be "healthy"
   ```

2. **Check database logs**:
   ```bash
   docker-compose logs postgres
   ```

3. **Restart database**:
   ```bash
   docker-compose restart postgres
   docker-compose restart api
   ```

## 🚀 Quick Fixes

### Restart Everything
```bash
docker-compose down
docker-compose up -d
```

### Check Logs
```bash
# All services
docker-compose logs --tail=50

# Just API
docker-compose logs api --tail=50 --follow
```

### Rebuild Containers
```bash
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

## 📋 Verification Checklist

- [ ] Docker containers are running (`docker-compose ps`)
- [ ] Port 8000 is mapped (`0.0.0.0:8000->8000/tcp`)
- [ ] API logs show "Application startup complete"
- [ ] `/health` endpoint returns 200
- [ ] `/` endpoint returns welcome message
- [ ] `/openapi.json` returns valid JSON
- [ ] `/docs` returns HTML (HTTP 200)

## 🎯 Expected Behavior

When everything is working correctly:

1. **Browser**: Opening `http://localhost:8000/docs` should show:
   - FastAPI Swagger UI interface
   - List of all API endpoints
   - Interactive API documentation
   - "Try it out" buttons for each endpoint

2. **Terminal**: Running `curl http://localhost:8000/docs` should return:
   - HTML content (starts with `<!DOCTYPE html>`)
   - HTTP status code 200

## 📞 Still Having Issues?

If you're still experiencing problems:

1. **Check container status**:
   ```bash
   docker-compose ps
   ```

2. **View all logs**:
   ```bash
   docker-compose logs --tail=100
   ```

3. **Check system resources**:
   ```bash
   docker stats
   ```

4. **Restart Docker daemon** (if needed):
   ```bash
   sudo systemctl restart docker  # Linux
   ```

5. **Verify Docker is running**:
   ```bash
   docker info
   ```

## ✅ Success Indicators

When everything is working, you should see:

```
✅ Containers: All Up
✅ Port 8000: Mapped and accessible
✅ API: Application startup complete
✅ Health: {"status":"healthy",...}
✅ Docs: HTML returned (HTTP 200)
```

If all these check out, your application is working correctly!

