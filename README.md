# 📱 OCR Telefon Numarası Çıkarıcı

PaddleOCR kullanarak görsellerden **5 ile başlayan 10 haneli Türk GSM numaralarını** otomatik olarak çıkaran Python projesi.

## ✨ Özellikler

- 🔍 PaddleOCR ile yüksek doğruluklu metin tanıma
- 📞 Regex ile akıllı telefon numarası filtreleme
- ⚙️ Yapılandırılabilir ayarlar (GPU/CPU, dil, güven eşiği)
- 🧪 Kapsamlı test suite
- 📁 Modüler ve profesyonel kod yapısı

## 📁 Proje Yapısı

```
emoproje/
├── src/
│   ├── __init__.py
│   ├── ocr_service.py          # PaddleOCR sarmalayıcı
│   ├── phone_extractor.py      # Telefon numarası çıkarıcı
│   └── utils.py                # Yardımcı fonksiyonlar
├── config/
│   └── settings.py             # Konfigürasyon
├── tests/
│   └── test_phone_extractor.py # Unit testler
├── images/                     # Test görselleri
├── main.py                     # Ana giriş noktası
├── requirements.txt
└── README.md
```

## 🚀 Kurulum

### 1. Virtual Environment Oluştur (Önerilen)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. (Opsiyonel) GPU Desteği

```bash
pip install paddlepaddle-gpu
```

## 💻 Kullanım

### Komut Satırından

```bash
# Tek görsel tara
python main.py --image images/sozlesme.jpg

# Verbose mod
python main.py --image images/sozlesme.jpg --verbose

# Tüm görselleri tara
python main.py --directory images/
```

### Python Kodu İçinden

```python
from src import OCRService, PhoneExtractor
from src.phone_extractor import extract_phone_numbers

# Hızlı kullanım
numbers = extract_phone_numbers("Sözleşme-5356314848")
print(numbers)  # ['5356314848']

# Detaylı kullanım
ocr = OCRService()
extractor = PhoneExtractor()

results = ocr.extract_text("gorsel.jpg")
phones = extractor.extract_from_ocr_results(results)

for phone in phones:
    print(f"Numara: {phone.formatted_number}")
    print(f"Güven: %{phone.confidence * 100:.2f}")
```

## 🧪 Test

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Coverage ile
python -m pytest tests/ --cov=src --cov-report=html
```

## ⚙️ Konfigürasyon

`config/settings.py` dosyasından ayarları değiştirebilirsiniz:

```python
# OCR Ayarları
ocr.language = 'en'       # Dil
ocr.device = 'cpu'        # 'cpu' veya 'gpu'
ocr.show_log = False      # Log göster

# Telefon Ayarları
phone.pattern = r'5\d{9}' # Regex deseni
phone.min_confidence = 0.5 # Minimum güven
```

## 📝 Regex Deseni

Proje, aşağıdaki regex desenini kullanır:

```
5\d{9}
```

Bu desen:
- `5` ile başlar (Türk GSM operatörleri)
- Ardından tam 9 rakam gelir
- Toplam 10 haneli numara

**Örnekler:**
| Girdi | Çıktı |
|-------|-------|
| `Sözleşme-5356314848` | `5356314848` |
| `Tel: (535) 631 48 48` | `5356314848` |
| `535-631-48-48` | `5356314848` |

## 📄 Lisans

MIT License

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın
