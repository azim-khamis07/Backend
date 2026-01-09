# Error Explanation: "Address already in use" (Port 8000)

## ❌ What the Error Means

```
ERROR: [Errno 98] Address already in use
```

This error means **port 8000 is already being used by another process**, so your FastAPI server cannot start.

### Common Causes:
1. ✅ Another instance of the server is already running
2. ✅ A previous server process didn't shut down properly
3. ✅ Another application is using port 8000

---

## 🔍 How to Check What's Using Port 8000

### Method 1: Using `lsof`
```bash
lsof -i :8000
```

### Method 2: Using `netstat`
```bash
netstat -tulpn | grep :8000
```

### Method 3: Using `ss`
```bash
ss -tulpn | grep :8000
```

### Method 4: Check for uvicorn processes
```bash
ps aux | grep uvicorn
```

---

## ✅ Solutions

### Solution 1: Kill the Process (Recommended)

#### Option A: Kill by port
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

#### Option B: Kill all uvicorn processes
```bash
pkill -9 -f "uvicorn.*app.main"
```

#### Option C: Force kill by port
```bash
fuser -k 8000/tcp
```

### Solution 2: Use a Different Port

If you can't kill the process, use a different port:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Then access:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Solution 3: Automatic Fix (Already Updated!)

The `start_server.sh` script has been **updated** to automatically:
1. ✅ Check if port 8000 is in use
2. ✅ Kill any existing process on that port
3. ✅ Start the server

Just run:
```bash
./start_server.sh
```

The script will handle everything automatically!

---

## 🔧 Quick Fix Commands

```bash
# One-liner to clear port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || pkill -9 -f "uvicorn.*app.main" 2>/dev/null || fuser -k 8000/tcp 2>/dev/null

# Wait a moment
sleep 2

# Verify port is free
lsof -i :8000
# (Should return nothing if port is free)

# Now start the server
./start_server.sh
```

---

## 📋 Updated start_server.sh

The script now includes automatic port cleanup:

```bash
# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use. Stopping existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
    sleep 2
    echo "✅ Port 8000 cleared"
fi
```

---

## ✅ Verify Server Started Successfully

After starting, check:

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","database":"connected","redis":"connected"}
```

If you see the health check response, the server is running! 🎉

---

## 🎯 Summary

**The Error:** Port 8000 is already in use  
**The Fix:** Kill the process using port 8000 (or use a different port)  
**The Solution:** The updated `start_server.sh` now handles this automatically!

**Just run:** `./start_server.sh` and it will work! ✅


