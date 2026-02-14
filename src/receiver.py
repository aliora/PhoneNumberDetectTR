"""
Receiver Service - FastAPI

Gelen OCR isteklerini kabul eder ve Redis queue'ya ekler.
Endpoints:
- POST /process: Yeni OCR işi ekle
- GET /result/{task_id}: Sonuç sorgula
- GET /status: Servis durumu
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from src.queue_manager import queue_manager
from config.settings import settings

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/receiver.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('receiver')

# FastAPI app
app = FastAPI(
    title="OCR Receiver Service",
    description="Turkish Contract Phone Number OCR - Request Handler",
    version="1.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response modelleri
class ProcessRequest(BaseModel):
    """OCR işleme isteği"""
    image_url: str
    user_id: str
    timestamp: str
    callback_url: Optional[str] = None
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('image_url must start with http:// or https://')
        return v
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('timestamp must be in ISO format')
        return v


class ProcessResponse(BaseModel):
    """OCR işleme yanıtı"""
    task_id: str
    status: str
    message: str
    enqueued_at: str
    queue_size: int


class ResultResponse(BaseModel):
    """Sonuç sorgulama yanıtı"""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Servis durumu"""
    service: str
    status: str
    redis_connected: bool
    queue_size: int
    timestamp: str


@app.post("/process", response_model=ProcessResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_image(request: ProcessRequest):
    """
    Yeni bir OCR işleme isteği oluştur
    
    Request body:
    {
        "image_url": "https://example.com/image.jpg",
        "user_id": "user123",
        "timestamp": "2026-02-14T10:30:00",
        "callback_url": "https://callback.example.com/webhook" (optional)
    }
    """
    try:
        # Redis bağlantı kontrolü
        if not queue_manager.health_check():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection failed"
            )
        
        # İşi kuyruğa ekle
        task_id = queue_manager.enqueue_job(
            image_url=request.image_url,
            user_id=request.user_id,
            timestamp=request.timestamp,
            callback_url=request.callback_url
        )
        
        queue_size = queue_manager.get_queue_size()
        
        logger.info(f"Job enqueued - task_id: {task_id}, user_id: {request.user_id}, queue_size: {queue_size}")
        
        return ProcessResponse(
            task_id=task_id,
            status="queued",
            message=f"Job successfully queued for processing",
            enqueued_at=datetime.now().isoformat(),
            queue_size=queue_size
        )
        
    except Exception as e:
        logger.error(f"Failed to enqueue job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue job: {str(e)}"
        )


@app.get("/result/{task_id}", response_model=ResultResponse)
async def get_result(task_id: str):
    """
    Task ID ile işleme sonucunu sorgula
    
    Returns:
    - status: "completed", "processing", "not_found", "error"
    - result: OCR sonuçları (varsa)
    """
    try:
        result = queue_manager.get_result(task_id)
        
        if result:
            logger.info(f"Result retrieved - task_id: {task_id}, status: {result.get('status')}")
            return ResultResponse(
                task_id=task_id,
                status=result.get('status', 'completed'),
                result=result if result.get('status') != 'error' else None,
                error=result.get('error') if result.get('status') == 'error' else None
            )
        else:
            # Sonuç bulunamadı - hala işleniyor olabilir
            logger.info(f"Result not found - task_id: {task_id}")
            return ResultResponse(
                task_id=task_id,
                status="processing",
                result=None,
                error=None
            )
            
    except Exception as e:
        logger.error(f"Failed to retrieve result for task_id {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve result: {str(e)}"
        )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Servis sağlık kontrolü"""
    redis_ok = queue_manager.health_check()
    queue_size = queue_manager.get_queue_size() if redis_ok else 0
    
    return StatusResponse(
        service="receiver",
        status="healthy" if redis_ok else "unhealthy",
        redis_connected=redis_ok,
        queue_size=queue_size,
        timestamp=datetime.now().isoformat()
    )


@app.get("/")
async def root():
    """API bilgisi"""
    return {
        "service": "OCR Receiver Service",
        "version": "1.0.0",
        "endpoints": {
            "POST /process": "Submit OCR job",
            "GET /result/{task_id}": "Query job result",
            "GET /status": "Service health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Receiver Service on {settings.api.receiver_host}:{settings.api.receiver_port}")
    
    uvicorn.run(
        app,
        host=settings.api.receiver_host,
        port=settings.api.receiver_port,
        log_level="info"
    )
