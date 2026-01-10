"""
OCR Sözleşme Numarası Çıkarma Modülü
"""

from .ocr_service import OCRService
from .phone_extractor import extract_contract_number

__all__ = ['OCRService', 'extract_contract_number']
