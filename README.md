# 🚗 Монгол машины дугаар таних систем (Mongolian ALPR)

Видео буюу камерын эх үүсвэрээс машины дугаарыг таних Python систем.

## ✨ Онцлог

✅ **Монгол кириллийн дугаарыг таних** (1234УБЗ формат)  
✅ **Real-time видео боловсруулалт** (камер, MP4, AVI болон бусад)  
✅ **GUI интерфэйс** (Tkinter ашиглан)  
✅ **Өндөр цэвэр** - EasyOCR + OpenCV ашиглаж зохистой нь сайжиргасан  
✅ **CSV, JSON экспорт** - түүхийг хадгалах  
✅ **Давхардал шалгалт** - ижил дугаарыг олон удаа таньдаггүй

## 📋 Шаардлага

- Python 3.8+
- Windows/Mac/Linux
- 4GB RAM (ideal: 8GB+)
- Вебкамер эсвэл видео файл

## 🔧 Суулгалт

### 1. Python виртуал орчин суулгах

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Сангуудыг суулгах

```bash
pip install -r requirements.txt
```

**⚠️ Эхний удаа** EasyOCR моделийг татан авахдаа интернет холболт хэрэгтэй (200MB+).

## 🚀 Ашиглалт

```bash
python mongolian_alpr.py
```

### GUI товчлуур

| Товчлуур         | Ажиллагаа             |
| ---------------- | --------------------- |
| 📂 Видео нээх    | MP4/AVI файл сонгох   |
| 📷 Камер         | Вебкамер ашиглах      |
| ⏹ Зогсоох        | Боловсруулалт зогсоох |
| 💾 CSV хадгалах  | .csv файлаар экспорт  |
| 📊 JSON хадгалах | .json файлаар экспорт |
| 🗑 Цэвэрлэх      | Өгөгдөл цэвэрлэх      |

## 📊 Гаралт

### CSV формат

```
text,confidence,bbox,time,frame_timestamp
1234УБЗ,0.92,"[120, 50, 200, 85]",14:23:45,2024-04-01T14:23:45.123456
```

### JSON формат

```json
[
  {
    "text": "1234УБЗ",
    "confidence": 0.92,
    "bbox": [120, 50, 200, 85],
    "time": "14:23:45",
    "frame_timestamp": "2024-04-01T14:23:45.123456"
  }
]
```

## 🔍 Дугаарын формат

Система энэ форматыг таних оновчтойгоор суулгагдсан:

- **4 цифр**: 0-9
- **3 Кириллийн үсэг**: А-Я, Ө, Ү

Жишээ:

- ✅ 1234УБЗ
- ✅ 5678ХОХ
- ❌ УБЗ1234 (буруу дараалал)

## ⚡ Хурдасгалт зөвлөмжүүд

### GPU ашиглах (эрс хурдан)

Хэрэв CUDA суулгасан бол `mongolian_alpr.py` доерхи мөрийг өөрчлөх:

```python
self.reader = easyocr.Reader(['en', 'mn'], gpu=True)  # gpu=False → True
```

### Frame processing хорчлох

13-р мөрийг өөрчлөх:

```python
if frame_count % 2 == 0:  # 2 → 3 (3 frame тутамд нэг боловсруулалт)
```

## 🐛 Асуудлын шийдэл

### "ModuleNotFoundError: No module named 'easyocr'"

```bash
pip install easyocr --upgrade
```

### Камер нээхгүй

- Windows: Камерын төхөөрөмж нэмэлтээр эрхүүлэх
- Linux: `v4l2-ctl` шалгах

### Удаан идэвхжүүлэлт

- Эхний удаа 30-60 сек хүлээх (моделийг ачаалаж байна)
- Дараа нь хэвийн ажиллах бөгөөд

### Монгол кириллийг таних хүнд

- CSV файлыг `utf-8-sig` кодчилолоор хадгалсан
- Кириллийн О (О) болон 0 (тэг)-ийг солих логик бүтэнн

## 📁 Файлын байршил

```
Plate detect py/
├── mongolian_alpr.py       # Үндсэн программ
├── requirements.txt         # Python сан
└── README.md               # Энэ файл
```

## 💡 Ипотез сайжруулах

### YOLOv8 ашиглах (илүү нарийн)

Roboflow дээрээс "license_plate_mongolia" dataset олоод:

```python
from ultralytics import YOLO
model = YOLO('yolov8m.pt')  # pre-trained model
results = model.predict(frame)
```

### Pytesseract хэрэглэх (хөнгөн)

```bash
pip install pytesseract
```

## 🗣️ Монгол хэл дэмжих

- ✅ Кириллийн үсэг (А-Я, Ө, Ү)
- ✅ Аравтын цифр (0-9)
- ✅ Англи байлга (хэрэгцээсэн үед)

## 📞 Техник дэмжлэг

Алдаа/сөргүүү Тулгалт:

1. `requirements.txt` дахиаг суулгах
2. Python 3.8+ эсэхийг шалгах
3. Интернет холболт шалгах (EasyOCR толь сан татаж авахаар)

---

**Сүүлийн шинэчлэл**: 2024-04-01
**Хувилбар**: 1.0

## Local Model Training

Use `TRAINING.md` for full local training steps:
- YOLOv8 plate detector training
- TrOCR OCR fine-tuning for `NNNNTTT` Mongolian plate text
