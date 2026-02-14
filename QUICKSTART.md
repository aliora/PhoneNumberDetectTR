# 🚀 Quick Start Guide

## Prerequisites
- **Python 3.8+**
- **Redis** (running on localhost:6379)

## Installation Steps

### 1. Install Redis (if not already installed)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Docker (Alternative):**
```bash
docker-compose up -d redis
```

### 2. Run Setup Script
```bash
bash scripts/setup.sh
```

This will:
- Install all Python dependencies
- Download OCR models
- Create necessary directories
- Verify environment

### 3. Start Services
```bash
bash scripts/start_services.sh
```

This starts:
- **Receiver API** (port 8001)
- **Sender Worker** (background)
- **Debug UI** (port 5000)

## Testing

### Option 1: Web Interface
Open in browser:
```
http://localhost:5000
```

Fill in:
- **Image URL**: Any publicly accessible image URL with Turkish contract number
- **User ID**: Any identifier (e.g., "test_user")
- **Timestamp**: Auto-filled

Click "Submit Job" and watch real-time processing!

### Option 2: API Testing
```bash
python3 scripts/test_services.py
```

### Option 3: Manual API Call
```bash
# Submit job
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "user_id": "test_user",
    "timestamp": "2026-02-14T12:00:00"
  }'

# Query result (replace TASK_ID)
curl http://localhost:8001/result/TASK_ID
```

## Stop Services
```bash
# Press Ctrl+C in the terminal running services
# OR
bash scripts/stop_services.sh
```

## Troubleshooting

### Redis not running?
```bash
redis-cli ping  # Should return "PONG"
```

### Port already in use?
Edit `config/settings.py` and change ports

### Services not starting?
Check logs:
```bash
tail -f logs/receiver.log
tail -f logs/sender.log
tail -f logs/debug_server.log
```

## Architecture

```
User → Debug UI (5000) → Receiver API (8001) → Redis Queue
                                                     ↓
                                          Sender Worker (OCR)
                                                     ↓
                                               Results (Redis)
```

## Key Endpoints

- `POST /process` - Submit OCR job
- `GET /result/{task_id}` - Query result
- `GET /status` - Health check

## What's New?

✅ **API-based**: No more CLI, use HTTP API  
✅ **Queue System**: Redis-backed job processing  
✅ **Microservices**: Receiver + Sender architecture  
✅ **Web UI**: Real-time testing interface  
✅ **Webhooks**: Callback support  
✅ **Scalable**: Add multiple workers easily  

## Documentation

- **Full Guide**: `MICROSERVICE_GUIDE.md`
- **Architecture**: `REFACTORING_SUMMARY.md`

---

**Need Help?** Check the logs or read the comprehensive guides!

🎉 **Enjoy your new microservice architecture!**
