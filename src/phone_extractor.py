"""
Telefon Numarası Çıkarıcı - Optimize Edilmiş

Sadece Sözleşme-5xxxxxxxxx desenine odaklanır.
"""

import re
from typing import Optional, Tuple

from config.settings import settings


def extract_contract_number(ocr_results: list) -> Tuple[Optional[str], float]:
    """
    OCR sonuçlarından Sözleşme numarasını çıkarır.
    
    Aradığı format: Sözleşme-5356314848 veya Sözleme-5356314848
    
    Args:
        ocr_results: OCR sonuç listesi
        
    Returns:
        (numara, güven_skoru) tuple - numara None olabilir
    """
    # Tüm metinleri ve skorları topla
    texts_with_scores = []
    for r in ocr_results:
        text = r.text if hasattr(r, 'text') else str(r)
        score = r.confidence if hasattr(r, 'confidence') else 0.0
        texts_with_scores.append((text, score))
    
    full_text = " ".join([t[0] for t in texts_with_scores])
    
    # Sözleşme-NUMARA desenini ara
    pattern = r'[Ss]özle[sş]me[-‐–—]?\s*(\d{10})'
    match = re.search(pattern, full_text)
    
    if match:
        number = match.group(1)
        if number.startswith('5'):
            # Bu numarayı içeren metnin skorunu bul
            for text, score in texts_with_scores:
                if number in text or f"Sözle" in text:
                    return number, score
            return number, 0.99
    
    # Yedek: Sadece 5 ile başlayan 10 haneli numara
    clean_text = re.sub(r'[^0-9]', '', full_text)
    pattern2 = r'5\d{9}'
    matches = re.findall(pattern2, clean_text)
    
    if matches:
        # En yüksek skorlu metinden al
        max_score = max([s for _, s in texts_with_scores]) if texts_with_scores else 0.0
        return matches[0], max_score
    
    return None, 0.0
