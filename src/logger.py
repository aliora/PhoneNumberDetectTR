"""
Log Yönetimi Modülü

OCR sonuçlarını dosyaya loglama işlemlerini yönetir.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import settings


class LogManager:
    """Log dosyası yönetim sınıfı"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Args:
            log_file: Log dosyası yolu (varsayılan: logs/ocr_results.log)
        """
        if log_file:
            self.log_path = Path(log_file)
        else:
            self.log_path = Path("logs/ocr_results.log")
        
        # Log dizinini oluştur
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str) -> None:
        """Mesajı log dosyasına yazar."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_line)
    
    def log_result(self, image_file: str, phone_numbers: list) -> None:
        """
        OCR sonucunu loglar.
        
        Format: dosya_adı: numara1, numara2, ...
        """
        if phone_numbers:
            numbers_str = ", ".join([p.formatted_number if hasattr(p, 'formatted_number') else str(p) for p in phone_numbers])
            self.log(f"{image_file}: {numbers_str}")
        else:
            self.log(f"{image_file}: Numara bulunamadı")
    
    def log_summary(self, total_files: int, total_numbers: int) -> None:
        """Özet bilgiyi loglar."""
        self.log(f"{'='*50}")
        self.log(f"ÖZET: {total_files} dosya tarandı, {total_numbers} numara bulundu")
        self.log(f"{'='*50}")
    
    def clear(self) -> None:
        """Log dosyasını temizler."""
        if self.log_path.exists():
            self.log_path.unlink()


def create_logger(log_file: Optional[str] = None) -> LogManager:
    """
    Kolaylık fonksiyonu: LogManager oluşturur.
    
    Args:
        log_file: Log dosyası yolu
        
    Returns:
        LogManager instance
    """
    return LogManager(log_file)
