"""
Sender Service - Worker

Redis queue'dan işleri alır, OCR işler ve sonuçları kaydeder.
Callback URL varsa webhook olarak bildirim gönderir.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import io
import logging
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from PIL import Image
from src.queue_manager import queue_manager
from src.ocr_service import OCRService
from src.phone_extractor import extract_contract_number
from config.settings import settings

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sender.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('sender')


class SenderWorker:
    """OCR işleme worker sınıfı"""
    
    def __init__(self):
        """Worker'ı başlat ve OCR servisini yükle"""
        logger.info("Initializing Sender Worker...")
        
        # OCR servisini singleton olarak yükle (model bir kere yüklenir)
        self.ocr_service = OCRService()
        logger.info("OCR Service loaded successfully")
        
        self.max_retries = settings.api.max_retries
        self.request_timeout = settings.api.request_timeout
        self.poll_interval = settings.api.sender_poll_interval
        
        # Redis bağlantı kontrolü
        if not queue_manager.health_check():
            raise Exception("Redis connection failed. Please check Redis server.")
        
        logger.info(f"Sender Worker initialized - polling interval: {self.poll_interval}s")
    
    def download_image(self, image_url: str) -> Optional[Image.Image]:
        """
        URL'den görseli indir
        
        Args:
            image_url: Görsel URL'i
        
        Returns:
            PIL Image veya None
        """
        try:
            response = requests.get(image_url, timeout=self.request_timeout)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))
            logger.info(f"Image downloaded successfully - size: {image.size}, mode: {image.mode}")
            return image
            
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {str(e)}")
            return None
    
    def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tek bir işi işle (OCR + phone extraction)
        
        Args:
            job_data: İş verisi
        
        Returns:
            İşlenmiş sonuç dictionary
        """
        task_id = job_data['task_id']
        image_url = job_data['image_url']
        user_id = job_data['user_id']
        timestamp = job_data['timestamp']
        
        logger.info(f"Processing job - task_id: {task_id}, user_id: {user_id}")
        
        start_time = time.time()
        
        try:
            # 1. Görseli indir
            image = self.download_image(image_url)
            if not image:
                raise Exception("Failed to download image")
            
            # 2. OCR işle
            ocr_result = self.ocr_service.process_image(image)
            
            if not ocr_result.success:
                raise Exception("OCR processing failed")
            
            # 3. Telefon numarasını çıkar (OCR sonuçlarından)
            phone_number, confidence = extract_contract_number(ocr_result.results)
            
            processing_time = time.time() - start_time
            
            # 4. Sonuç oluştur
            result = {
                'task_id': task_id,
                'status': 'completed',
                'user_id': user_id,
                'timestamp': timestamp,
                'image_url': image_url,
                'phone_number': phone_number,
                'confidence': confidence,
                'ocr_text': ocr_result.text[:500],  # İlk 500 karakter
                'processing_time': round(processing_time, 2),
                'processed_at': datetime.now().isoformat()
            }
            
            logger.info(
                f"Job completed - task_id: {task_id}, "
                f"phone: {phone_number}, confidence: {confidence:.2f}, "
                f"time: {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            error_result = {
                'task_id': task_id,
                'status': 'error',
                'user_id': user_id,
                'timestamp': timestamp,
                'image_url': image_url,
                'error': str(e),
                'processing_time': round(processing_time, 2),
                'processed_at': datetime.now().isoformat()
            }
            
            logger.error(f"Job failed - task_id: {task_id}, error: {str(e)}")
            
            return error_result
    
    def send_callback(self, callback_url: str, result: Dict[str, Any]) -> bool:
        """
        Webhook callback gönder
        
        Args:
            callback_url: Webhook URL'i
            result: Sonuç verisi
        
        Returns:
            Başarılı ise True
        """
        try:
            response = requests.post(
                callback_url,
                json=result,
                timeout=self.request_timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            logger.info(f"Callback sent successfully - task_id: {result['task_id']}, url: {callback_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send callback - task_id: {result['task_id']}, error: {str(e)}")
            return False
    
    def run(self):
        """Worker'ı sürekli çalıştır (main loop)"""
        logger.info("Sender Worker started - waiting for jobs...")
        
        while True:
            try:
                # Queue'dan iş al (blocking, timeout ile)
                job_data = queue_manager.dequeue_job(timeout=int(self.poll_interval))
                
                if not job_data:
                    continue
                
                # İşi işle
                result = self.process_job(job_data)
                
                # Sonucu Redis'e kaydet
                queue_manager.store_result(job_data['task_id'], result)
                
                # Callback URL varsa bildirim gönder
                if job_data.get('callback_url'):
                    self.send_callback(job_data['callback_url'], result)
                
                # Hata durumunda retry kontrolü
                if result['status'] == 'error':
                    retry_count = job_data.get('retry_count', 0)
                    if retry_count < self.max_retries:
                        logger.info(
                            f"Requeueing failed job - task_id: {job_data['task_id']}, "
                            f"retry: {retry_count + 1}/{self.max_retries}"
                        )
                        queue_manager.requeue_job(job_data)
                    else:
                        logger.warning(
                            f"Max retries reached - task_id: {job_data['task_id']}"
                        )
                
            except KeyboardInterrupt:
                logger.info("Sender Worker shutting down...")
                break
            
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {str(e)}")
                time.sleep(self.poll_interval)


def main():
    """Worker'ı başlat"""
    try:
        worker = SenderWorker()
        worker.run()
    except Exception as e:
        logger.error(f"Failed to start Sender Worker: {str(e)}")
        raise


if __name__ == "__main__":
    main()
