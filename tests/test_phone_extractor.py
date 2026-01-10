"""
Telefon Numarası Çıkarıcı Test Modülü

PhoneExtractor sınıfı için unit testler.
"""

import pytest
from src.phone_extractor import PhoneExtractor, extract_phone_numbers


class TestPhoneExtractor:
    """PhoneExtractor sınıfı testleri"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        self.extractor = PhoneExtractor()
    
    def test_basic_phone_extraction(self):
        """Basit telefon numarası çıkarma testi"""
        text = "5001234567"
        result = self.extractor.find_phone_in_text(text)
        assert result == ["5001234567"]
    
    def test_phone_with_prefix(self):
        """Sözleşme-5001234567 formatı testi"""
        text = "Sözleşme-5001234567"
        result = self.extractor.find_phone_in_text(text)
        assert result == ["5001234567"]
    
    def test_phone_with_spaces(self):
        """Boşluklu format testi"""
        text = "500 123 45 67"
        result = self.extractor.find_phone_in_text(text)
        assert result == ["5001234567"]
    
    def test_phone_with_parentheses(self):
        """Parantezli format testi"""
        text = "(500) 123 45 67"
        result = self.extractor.find_phone_in_text(text)
        assert result == ["5001234567"]
    
    def test_phone_with_dashes(self):
        """Tireli format testi"""
        text = "500-123-45-67"
        result = self.extractor.find_phone_in_text(text)
        assert result == ["5001234567"]
    
    def test_multiple_phones(self):
        """Birden fazla numara testi"""
        text = "Tel1: 5351234567, Tel2: 5429876543"
        result = self.extractor.find_phone_in_text(text)
        assert "5351234567" in result
        assert "5429876543" in result
    
    def test_no_phone_found(self):
        """Numara bulunamama testi"""
        text = "Bu metinde telefon yok"
        result = self.extractor.find_phone_in_text(text)
        assert result == []
    
    def test_invalid_phone_format(self):
        """Geçersiz format testi (5 ile başlamayan)"""
        text = "1234567890"
        result = self.extractor.find_phone_in_text(text)
        assert result == []
    
    def test_short_phone(self):
        """Kısa numara testi (10 haneden az)"""
        text = "535123456"  # 9 hane
        result = self.extractor.find_phone_in_text(text)
        assert result == []
    
    def test_clean_text(self):
        """Metin temizleme testi"""
        text = "Tel: (500) 123-45-67"
        result = self.extractor.clean_text(text)
        assert result == "5001234567"


class TestExtractPhoneNumbersFunction:
    """extract_phone_numbers fonksiyonu testleri"""
    
    def test_convenience_function(self):
        """Kolaylık fonksiyonu testi"""
        result = extract_phone_numbers("Sözleşme-5001234567")
        assert result == ["5001234567"]
    
    def test_empty_string(self):
        """Boş string testi"""
        result = extract_phone_numbers("")
        assert result == []
    
    def test_only_text(self):
        """Sadece metin testi"""
        result = extract_phone_numbers("Merhaba Dünya")
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
