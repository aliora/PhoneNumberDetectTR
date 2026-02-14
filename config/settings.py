"""
Uygulama Konfigürasyon Ayarları - Optimize Edilmiş

Sadece Sözleşme numarası çıkarmaya odaklanmış hızlı konfigürasyon.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class OCRSettings:
    """PaddleOCR yapılandırma ayarları - Hızlı mod"""
    language: str = 'en'
    device: Literal['cpu', 'gpu'] = 'cpu'
    # Hafif model kullan
    use_angle_cls: bool = False  # Açı sınıflandırma kapalı (hız için)
    det_model_dir: str = None  # Varsayılan hafif model
    rec_model_dir: str = None


@dataclass
class PhoneSettings:
    """Telefon numarası çıkarma ayarları"""
    # Sözleşme-5xxxxxxxxx deseni
    contract_pattern: str = r'[Ss]özle[sş]me[-‐–—]?\s*(\d{10})'
    # Sadece 5 ile başlayan numara deseni (yedek)
    phone_pattern: str = r'5\d{9}'
    # Minimum güven skoru
    min_confidence: float = 0.3
    # Başına 0 EKLEME
    add_leading_zero: bool = False


@dataclass
class RedisSettings:
    """Redis bağlantı ayarları"""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: str = None
    # Queue isimleri
    input_queue: str = 'ocr:input'
    output_prefix: str = 'ocr:output'
    # Sonuç TTL (saniye)
    result_ttl: int = 3600  # 1 saat


@dataclass
class APISettings:
    """API servis ayarları"""
    receiver_host: str = '0.0.0.0'
    receiver_port: int = 8001
    sender_poll_interval: float = 1.0  # saniye
    debug_host: str = '0.0.0.0'
    debug_port: int = 5001  # Changed from 5000 to avoid conflict with macOS AirPlay
    max_retries: int = 3
    request_timeout: int = 30  # saniye


@dataclass
class Settings:
    """Ana konfigürasyon sınıfı"""
    ocr: OCRSettings = field(default_factory=OCRSettings)
    phone: PhoneSettings = field(default_factory=PhoneSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    api: APISettings = field(default_factory=APISettings)
    
    # Desteklenen görsel formatları
    supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')


# Global konfigürasyon instance'ı
settings = Settings()
