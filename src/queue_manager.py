"""
Redis Queue Manager

Redis tabanlı FIFO queue yönetimi:
- Input queue: Gelen işleme istekleri
- Output queue: İşlenmiş sonuçlar (task_id bazlı)
"""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import redis
from config.settings import settings


class QueueManager:
    """Redis queue operasyonlarını yöneten singleton sınıf"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Redis bağlantısı
        self.redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True
        )
        
        self.input_queue = settings.redis.input_queue
        self.output_prefix = settings.redis.output_prefix
        self.result_ttl = settings.redis.result_ttl
        
        self._initialized = True
    
    def enqueue_job(self, image_url: str, user_id: str, timestamp: str, 
                    callback_url: Optional[str] = None) -> str:
        """
        Yeni bir OCR işini kuyruğa ekle
        
        Args:
            image_url: İşlenecek görsel URL'i
            user_id: Kullanıcı ID'si
            timestamp: Gönderim zamanı
            callback_url: Sonuç webhook URL'i (opsiyonel)
        
        Returns:
            task_id: Benzersiz iş ID'si
        """
        task_id = str(uuid.uuid4())
        
        job_data = {
            'task_id': task_id,
            'image_url': image_url,
            'user_id': user_id,
            'timestamp': timestamp,
            'callback_url': callback_url,
            'enqueued_at': datetime.now().isoformat(),
            'retry_count': 0
        }
        
        # JSON olarak input queue'ya ekle (FIFO - sağdan push, soldan pop)
        self.redis_client.rpush(self.input_queue, json.dumps(job_data))
        
        return task_id
    
    def dequeue_job(self, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """
        Kuyruktan bir iş al (blocking)
        
        Args:
            timeout: Bekleme süresi (0 = bloklamadan, None = sonsuz bekle)
        
        Returns:
            Job dictionary veya None
        """
        if timeout == 0:
            # Non-blocking pop
            result = self.redis_client.lpop(self.input_queue)
        else:
            # Blocking pop
            result = self.redis_client.blpop(self.input_queue, timeout=timeout)
            if result:
                _, result = result  # blpop returns (queue_name, value)
        
        if result:
            return json.loads(result)
        return None
    
    def store_result(self, task_id: str, result_data: Dict[str, Any]):
        """
        İşlenmiş sonucu kaydet
        
        Args:
            task_id: İş ID'si
            result_data: Sonuç verisi
        """
        key = f"{self.output_prefix}:{task_id}"
        result_data['completed_at'] = datetime.now().isoformat()
        
        # JSON olarak kaydet ve TTL ayarla
        self.redis_client.setex(
            key,
            self.result_ttl,
            json.dumps(result_data)
        )
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Task ID ile sonuç getir
        
        Args:
            task_id: İş ID'si
        
        Returns:
            Sonuç dictionary veya None
        """
        key = f"{self.output_prefix}:{task_id}"
        result = self.redis_client.get(key)
        
        if result:
            return json.loads(result)
        return None
    
    def requeue_job(self, job_data: Dict[str, Any]):
        """
        Başarısız işi tekrar kuyruğa ekle
        
        Args:
            job_data: İş verisi
        """
        job_data['retry_count'] = job_data.get('retry_count', 0) + 1
        self.redis_client.rpush(self.input_queue, json.dumps(job_data))
    
    def get_queue_size(self) -> int:
        """Input queue boyutunu döndür"""
        return self.redis_client.llen(self.input_queue)
    
    def health_check(self) -> bool:
        """Redis bağlantısını kontrol et"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def clear_queue(self):
        """Queue'yu temizle (debug için)"""
        self.redis_client.delete(self.input_queue)
    
    def get_all_results(self, pattern: str = "*") -> Dict[str, Any]:
        """Tüm sonuçları getir (debug için)"""
        keys = self.redis_client.keys(f"{self.output_prefix}:{pattern}")
        results = {}
        
        for key in keys:
            task_id = key.split(':')[-1]
            result = self.redis_client.get(key)
            if result:
                results[task_id] = json.loads(result)
        
        return results


# Singleton instance
queue_manager = QueueManager()
