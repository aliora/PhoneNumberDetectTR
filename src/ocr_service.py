"""
OCR Servis Modülü - Optimize Edilmiş

Hızlı OCR için minimal işlem + görsel boyutlandırma.
"""

import cv2
import numpy as np
from paddleocr import PaddleOCR
from typing import Optional
from dataclasses import dataclass

from config.settings import settings

# Maksimum görsel boyutu (hız için)
MAX_IMAGE_SIZE = 720


@dataclass
class OCRResult:
    """Tek bir OCR sonucu"""
    text: str
    confidence: float


class OCRService:
    """Hızlı PaddleOCR servis sınıfı"""
    
    _instance = None
    _ocr = None
    
    def __new__(cls):
        """Singleton pattern - model bir kez yüklensin"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """OCR modelini başlatır (sadece ilk seferde)"""
        if OCRService._ocr is None:
            OCRService._ocr = PaddleOCR(
                lang=settings.ocr.language,
                device=settings.ocr.device
            )
    
    def resize_image(self, img: np.ndarray) -> np.ndarray:
        """
        Görseli küçült (hız optimizasyonu).
        
        Args:
            img: Orijinal görsel
            
        Returns:
            Küçültülmüş görsel
        """
        h, w = img.shape[:2]
        
        # Zaten küçükse dokunma
        if max(h, w) <= MAX_IMAGE_SIZE:
            return img
        
        # Oranı koru
        if h > w:
            new_h = MAX_IMAGE_SIZE
            new_w = int(w * (MAX_IMAGE_SIZE / h))
        else:
            new_w = MAX_IMAGE_SIZE
            new_h = int(h * (MAX_IMAGE_SIZE / w))
        
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    def extract_text(self, image_path: str) -> list[OCRResult]:
        """
        Görselden metin çıkarır.
        
        Args:
            image_path: Görsel dosya yolu
            
        Returns:
            OCRResult listesi
        """
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        # Görseli küçült (hız için)
        img = self.resize_image(img)
        
        result = self._ocr.ocr(img)
        
        if result is None or len(result) == 0:
            return []
        
        ocr_results = []
        ocr_result_obj = result[0]
        
        # Yeni PaddleOCR yapısı
        if hasattr(ocr_result_obj, 'get'):
            rec_texts = ocr_result_obj.get('rec_texts', [])
            rec_scores = ocr_result_obj.get('rec_scores', [])
            
            for i, text in enumerate(rec_texts):
                score = rec_scores[i] if i < len(rec_scores) else 0.0
                if text and score >= settings.phone.min_confidence:
                    ocr_results.append(OCRResult(text=str(text), confidence=float(score)))
        
        return ocr_results
    
    def process_image(self, image) -> 'ProcessedOCRResult':
        """
        PIL Image veya numpy array'den metin çıkarır.
        
        Args:
            image: PIL Image veya numpy array
            
        Returns:
            ProcessedOCRResult with success status and text/results
        """
        try:
            # PIL Image ise numpy array'e çevir
            if hasattr(image, 'convert'):
                # PIL Image
                img = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
            else:
                img = image
            
            # Görseli küçült (hız için)
            img = self.resize_image(img)
            
            result = self._ocr.ocr(img)
            
            if result is None or len(result) == 0:
                return ProcessedOCRResult(success=False, text="", results=[])
            
            ocr_results = []
            ocr_result_obj = result[0]
            
            # Yeni PaddleOCR yapısı
            if hasattr(ocr_result_obj, 'get'):
                rec_texts = ocr_result_obj.get('rec_texts', [])
                rec_scores = ocr_result_obj.get('rec_scores', [])
                
                for i, text in enumerate(rec_texts):
                    score = rec_scores[i] if i < len(rec_scores) else 0.0
                    if text and score >= settings.phone.min_confidence:
                        ocr_results.append(OCRResult(text=str(text), confidence=float(score)))
            
            # Tüm metni birleştir
            full_text = " ".join([r.text for r in ocr_results])
            
            return ProcessedOCRResult(
                success=True if ocr_results else False,
                text=full_text,
                results=ocr_results
            )
        except Exception as e:
            return ProcessedOCRResult(success=False, text="", results=[], error=str(e))


@dataclass
class ProcessedOCRResult:
    """İşlenmiş OCR sonucu"""
    success: bool
    text: str
    results: list = None
    error: str = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
