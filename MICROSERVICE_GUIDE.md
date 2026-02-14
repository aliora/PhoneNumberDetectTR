# OCR Microservice Architecture - Quick Start Guide

## 🏗️ Architecture Overview

This project has been refactored into a microservice architecture with three main components:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │ ───> │   Receiver   │ ───> │    Redis    │
│   (Debug    │      │   (FastAPI)  │      │    Queue    │
│     UI)     │      │   Port 8001  │      │             │
└─────────────┘      └──────────────┘      └─────────────┘
       ▲                                            │
       │                                            │
       │             ┌──────────────┐               │
       └──────────── │    Sender    │ <─────────────┘
          Webhook    │   (Worker)   │
          Callback   │  + OCR Model │
                     └──────────────┘
```

### Components:

1. **Receiver Service** (`src/receiver.py`) - Port 8001
   - FastAPI service that accepts image processing requests
   - Validates input and enqueues jobs to Redis
   - Provides result query endpoints
   - Returns immediately with task_id (non-blocking)

2. **Sender Worker** (`src/sender.py`)
   - Background worker that processes jobs sequentially
   - Downloads images from URLs
   - Runs OCR using PaddleOCR (singleton, loaded once)
   - Extracts Turkish contract phone numbers
   - Stores results in Redis with TTL (1 hour)
   - Sends webhook callbacks when completed

3. **Debug Web UI** (`debug/server.py`) - Port 5000
   - Flask-based testing interface
   - Submit test jobs with image URL, user ID, timestamp
   - Real-time result polling and webhook reception
   - Service health monitoring
   - View all cached results

4. **Redis Queue** (`src/queue_manager.py`)
   - FIFO job queue (`ocr:input`)
   - Result storage with TTL (`ocr:output:{task_id}`)
   - Automatic retry mechanism (max 3 attempts)

## 🚀 Quick Start

### Prerequisites

1. **Redis** must be installed and running:
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Linux
   sudo apt install redis-server
   sudo systemctl start redis
   
   # Verify Redis is running
   redis-cli ping  # Should return "PONG"
   ```

2. **Python 3.8+** with pip

### Installation & Running

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start all services** (single command):
   ```bash
   bash scripts/start_services.sh
   ```
   
   This will:
   - Check Redis connection
   - Start Receiver API on port 8001
   - Start Sender Worker in background
   - Start Debug UI on port 5000
   - Show real-time logs from all services

3. **Open Debug UI**:
   ```
   http://localhost:5000
   ```

4. **Stop all services**:
   ```bash
   # Press Ctrl+C in the terminal running start_services.sh
   # OR run:
   bash scripts/stop_services.sh
   ```

## 📡 API Usage

### Submit OCR Job

**Endpoint**: `POST http://localhost:8001/process`

**Request Body**:
```json
{
  "image_url": "https://example.com/contract-image.jpg",
  "user_id": "user123",
  "timestamp": "2026-02-14T10:30:00",
  "callback_url": "http://your-server.com/webhook" (optional)
}
```

**Response** (202 Accepted):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Job successfully queued for processing",
  "enqueued_at": "2026-02-14T10:30:01.123456",
  "queue_size": 1
}
```

### Query Result

**Endpoint**: `GET http://localhost:8001/result/{task_id}`

**Response** (Completed):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "user_id": "user123",
    "timestamp": "2026-02-14T10:30:00",
    "image_url": "https://example.com/contract-image.jpg",
    "phone_number": "5356314848",
    "confidence": 0.95,
    "ocr_text": "Sözleşme-5356314848...",
    "processing_time": 2.34,
    "processed_at": "2026-02-14T10:30:03.456789"
  }
}
```

**Response** (Processing):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "result": null
}
```

**Response** (Error):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "error",
  "result": null,
  "error": "Failed to download image"
}
```

### Service Health Check

**Endpoint**: `GET http://localhost:8001/status`

**Response**:
```json
{
  "service": "receiver",
  "status": "healthy",
  "redis_connected": true,
  "queue_size": 3,
  "timestamp": "2026-02-14T10:30:00"
}
```

## 🧪 Testing with Debug UI

1. Open `http://localhost:5000` in your browser
2. Fill in the form:
   - **Image URL**: URL to a contract image (must be publicly accessible)
   - **User ID**: Any identifier (e.g., "test_user_1")
   - **Timestamp**: Auto-filled with current time
3. Click **Submit Job**
4. Task ID will be auto-filled in the query section
5. Click **Start Polling** to watch real-time processing
6. View results including:
   - Extracted phone number
   - Confidence score
   - Processing time
   - OCR text preview

## 📊 Webhook Callbacks

If you provide a `callback_url` when submitting a job, the Sender will POST the result to that URL when processing completes:

**Webhook POST to your URL**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "user_id": "user123",
  "timestamp": "2026-02-14T10:30:00",
  "image_url": "https://example.com/image.jpg",
  "phone_number": "5356314848",
  "confidence": 0.95,
  "ocr_text": "Sözleşme-5356314848...",
  "processing_time": 2.34,
  "processed_at": "2026-02-14T10:30:03.456789"
}
```

The debug UI automatically registers itself as the callback endpoint to demonstrate this feature.

## 📝 Log Files

All services write logs to the `logs/` directory:

- `logs/receiver.log` - Receiver API logs
- `logs/sender.log` - Sender worker logs  
- `logs/debug_server.log` - Debug UI logs

Use the start script to see live logs, or view them directly:
```bash
tail -f logs/receiver.log
tail -f logs/sender.log
tail -f logs/debug_server.log
```

## ⚙️ Configuration

Edit `config/settings.py` to customize:

- **Redis connection**: host, port, password
- **API ports**: receiver (8001), debug UI (5000)
- **Queue names**: input queue, output prefix
- **Result TTL**: how long results are stored (default: 1 hour)
- **Retry settings**: max retries, timeouts
- **OCR settings**: language, device (CPU/GPU)

## 🔧 Troubleshooting

### Redis connection failed
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Port already in use
```bash
# Find process using port 8001
lsof -i :8001

# Kill process
kill -9 <PID>

# Or change port in config/settings.py
```

### OCR model not loading
```bash
# Reinstall PaddleOCR
pip uninstall paddleocr paddlepaddle
pip install paddleocr>=2.7.0 paddlepaddle>=2.5.0
```

### Services not stopping
```bash
# Force stop all services
bash scripts/stop_services.sh

# Manually kill processes
ps aux | grep "receiver.py\|sender.py\|debug/server.py"
kill -9 <PID>
```

## 🎯 Development Notes

- **Sequential Processing**: Sender processes one job at a time (maintains AI model in memory)
- **Result Caching**: Results expire after 1 hour (configurable)
- **Retry Logic**: Failed jobs retry up to 3 times with exponential backoff
- **Webhook Timeout**: 30 seconds (configurable)
- **Image Download**: 30 second timeout with proper error handling

## 📦 Project Structure

```
PhoneNumberDetectTR/
├── config/
│   └── settings.py          # Configuration (Redis, API, OCR)
├── src/
│   ├── queue_manager.py     # Redis queue operations
│   ├── receiver.py          # FastAPI receiver service
│   ├── sender.py            # Worker with OCR processing
│   ├── ocr_service.py       # PaddleOCR singleton
│   └── phone_extractor.py   # Phone number extraction
├── debug/
│   ├── server.py            # Flask debug server
│   ├── index.html           # Test web interface
│   └── static/
│       └── style.css        # UI styling
├── scripts/
│   ├── start_services.sh    # Start all services
│   └── stop_services.sh     # Stop all services
├── logs/                    # Service logs
└── requirements.txt         # Python dependencies
```

## 📄 License

Same as original project license.

---

**Need help?** Check the logs or open an issue with detailed error messages.
