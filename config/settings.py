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
class Settings:
    """Ana konfigürasyon sınıfı"""
    ocr: OCRSettings = field(default_factory=OCRSettings)
    phone: PhoneSettings = field(default_factory=PhoneSettings)
    
    # Desteklenen görsel formatları
    supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')


# Global konfigürasyon instance'ı
settings = Settings()
