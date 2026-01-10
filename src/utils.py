"""
Yardımcı Fonksiyonlar Modülü

Genel amaçlı utility fonksiyonları içerir.
"""

import os
from pathlib import Path
from typing import Optional

from config.settings import settings


def validate_image_path(image_path: str) -> tuple[bool, Optional[str]]:
    """
    Görsel dosya yolunu doğrular.
    
    Args:
        image_path: Kontrol edilecek dosya yolu
        
    Returns:
        (geçerli_mi, hata_mesajı) tuple'ı
    """
    path = Path(image_path)
    
    if not path.exists():
        return False, f"Dosya bulunamadı: {image_path}"
    
    if not path.is_file():
        return False, f"Geçerli bir dosya değil: {image_path}"
    
    suffix = path.suffix.lower()
    if suffix not in settings.supported_formats:
        return False, f"Desteklenmeyen format: {suffix}. Desteklenen: {settings.supported_formats}"
    
    return True, None


def format_phone_number(number: str, with_country_code: bool = False) -> str:
    """
    Telefon numarasını formatlar.
    
    Args:
        number: 10 haneli numara (5XXXXXXXXX)
        with_country_code: Ülke kodu eklensin mi
        
    Returns:
        Formatlanmış numara
        
    Example:
        >>> format_phone_number("5356314848")
        '0535 631 48 48'
        >>> format_phone_number("5356314848", with_country_code=True)
        '+90 535 631 48 48'
    """
    if len(number) != 10:
        return number
    
    # 5XX XXX XX XX formatı
    formatted = f"{number[0:3]} {number[3:6]} {number[6:8]} {number[8:10]}"
    
    if with_country_code:
        return f"+90 {formatted}"
    else:
        return f"0{formatted}"


def print_results(phone_matches: list, verbose: bool = True) -> None:
    """
    Bulunan telefon numaralarını konsola yazdırır.
    
    Args:
        phone_matches: PhoneMatch listesi
        verbose: Detaylı çıktı mı
    """
    if not phone_matches:
        print("\n[BİLGİ] Hiç telefon numarası bulunamadı.")
        return
    
    print(f"\n{'='*50}")
    print(f"[SONUÇ] {len(phone_matches)} adet telefon numarası bulundu:")
    print(f"{'='*50}")
    
    for i, match in enumerate(phone_matches, 1):
        if verbose and hasattr(match, 'confidence'):
            print(f"\n  {i}. Numara: {match.formatted_number}")
            print(f"     Ham: {match.number}")
            print(f"     Güven: %{match.confidence * 100:.2f}")
            print(f"     Kaynak: {match.original_text}")
        else:
            # Basit string listesi için
            formatted = format_phone_number(match) if isinstance(match, str) else match.formatted_number
            print(f"  {i}. {formatted}")
    
    print(f"\n{'='*50}")


def get_project_root() -> Path:
    """Proje kök dizinini döndürür."""
    return Path(__file__).parent.parent


def ensure_directory_exists(directory: str) -> None:
    """Dizinin var olduğundan emin olur, yoksa oluşturur."""
    Path(directory).mkdir(parents=True, exist_ok=True)
