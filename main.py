#!/usr/bin/env python3
"""
OCR Sözleşme Numarası Çıkarıcı - Optimize Edilmiş

Kullanım:
    python main.py                    # images/ klasörünü tara
    python main.py -d test/           # test/ klasörünü tara
    python main.py -i gorsel.jpg      # tek görsel
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ocr_service import OCRService
from src.phone_extractor import extract_contract_number
from config.settings import settings

# Varsayılan dizin
DEFAULT_DIR = "images"
LOG_FILE = "logs/ocr_results.log"


def log_result(filename: str, number: str, confidence: float):
    """Sonucu log dosyasına yaz."""
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {filename}: {number} (güven: %{confidence*100:.0f})\n")


def scan_image(image_path: str, ocr: OCRService) -> tuple[str, float, float]:
    """Tek görsel tara, (numara, güven, süre) döndür."""
    start = time.time()
    results = ocr.extract_text(image_path)
    elapsed = time.time() - start
    
    if not results:
        return None, 0.0, elapsed
    number, confidence = extract_contract_number(results)
    return number, confidence, elapsed


def main():
    parser = argparse.ArgumentParser(description="Sözleşme numarası çıkarıcı")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--image", help="Tek görsel")
    group.add_argument("-d", "--directory", help="Dizin")
    parser.add_argument("-l", "--log", action="store_true", help="Log dosyasına yaz")
    args = parser.parse_args()
    
    total_start = time.time()
    
    print("\n📱 Sözleşme Numarası Çıkarıcı")
    print("=" * 40)
    
    # OCR bir kez yükle
    model_start = time.time()
    print("[...] OCR modeli yükleniyor...")
    ocr = OCRService()
    model_time = time.time() - model_start
    print(f"[OK] Model hazır ({model_time:.1f}s)\n")
    
    results = {}
    scan_times = []
    
    if args.image:
        # Tek görsel
        number, confidence, elapsed = scan_image(args.image, ocr)
        name = Path(args.image).name
        scan_times.append(elapsed)
        if number:
            results[name] = (number, confidence)
            print(f"✓ {name}: {number} (güven: %{confidence*100:.0f}, {elapsed:.2f}s)")
        else:
            print(f"✗ {name}: Bulunamadı ({elapsed:.2f}s)")
    else:
        # Dizin tara
        directory = args.directory or DEFAULT_DIR
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"[HATA] Dizin bulunamadı: {directory}")
            return
        
        # Görselleri bul
        images = []
        for ext in settings.supported_formats:
            images.extend(dir_path.glob(f"*{ext}"))
        
        if not images:
            print(f"[!] {directory}/ içinde görsel yok")
            return
        
        print(f"[i] {len(images)} görsel bulundu\n")
        
        for img in sorted(images):
            number, confidence, elapsed = scan_image(str(img), ocr)
            scan_times.append(elapsed)
            if number:
                results[img.name] = (number, confidence)
                print(f"✓ {img.name}: {number} (güven: %{confidence*100:.0f}, {elapsed:.2f}s)")
            else:
                print(f"✗ {img.name}: - ({elapsed:.2f}s)")
    
    # Özet
    total_time = time.time() - total_start
    avg_time = sum(scan_times) / len(scan_times) if scan_times else 0
    
    print(f"\n{'='*40}")
    print(f"Toplam: {len(results)} numara bulundu")
    print(f"⏱ Süre: {total_time:.1f}s (ortalama: {avg_time:.2f}s/görsel)")
    
    # Log
    if args.log and results:
        for name, (num, conf) in results.items():
            log_result(name, num, conf)
        print(f"[LOG] {LOG_FILE}")


if __name__ == "__main__":
    main()