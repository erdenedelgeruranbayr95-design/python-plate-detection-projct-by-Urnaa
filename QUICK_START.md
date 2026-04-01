# ⚡ Хурдан эхлүүлэлтийн гарын авлага

## 1️⃣ Python суулгах

1. [python.org](https://www.python.org) дээрээс Python 3.8 вдээс дээш хүүхлэх
2. Windows-д суулгахдаа **"Add Python to PATH"** сонгоно

## 2️⃣ Проектын фолдор нээх

```bash
cd "C:\Users\Dell Inspiron 3535\OneDrive\Desktop\Plate detect py"
```

## 3️⃣ Виртуал орчин үүсгэх

```bash
python -m venv venv
```

Идэвхжүүлэх:

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Идэвхжүүлэлтээ шалгах (командын эхлэлд "(venv)" гарч ирэх база):

```
(venv) C:\Users\...\Plate detect py>
```

## 4️⃣ Сангуудыг суулгах

```bash
pip install -r requirements.txt
```

**⏳ Эхний удаа 5-10 минут хүлээнэ үү** (EasyOCR модель татан авча байна ~ 200MB)

Баталгаажуулах:

```bash
python -c "import cv2, easyocr, tkinter; print('✓ Амжилттай!')"
```

## 5️⃣ Программ ажилуулах

### GUI ашиглан (сонгогдсон):

```bash
python mongolian_alpr.py
```

### Командын мөрөөс (batch):

```bash
# Видео файлаа:
python batch_processor.py -i video.mp4 -o results.csv

# Камер:
python batch_processor.py -i 0 -o camera_results.csv

# GPU ашиглах:
python batch_processor.py -i video.mp4 -o results.csv --gpu
```

## 🎯 Эхний тести

1. GUI нээгдэх үед **"📷 Камер"** товчлуур дарна
2. Камер идэвхижвэл **"✓ Бэлэн байна..."** гарч ирнэ
3. Машины дугаар яриулна → GUI-д гарч ирнэ
4. **"⏹ Зогсоох"** дарна
5. **"💾 CSV хадгалах"** дарт CSV файлаар aлга

## ❌ Асуудал үүссэн бол

### ModuleNotFoundError

```bash
pip install easyocr opencv-python pillow pandas numpy
```

### Камер ажилахгүй

- Windows: Камер нэмэлтээр эрхүүлсэн эсэх
- Linux: `sudo apt install v4l-utils`
- Mac: Системийн энивьер дээр камер эрхүүлсэн байх

### Удаан идэвхжүүлэлт

- Эхний удаа хэвийн → **30-60 сек хүлээх**
- Дараа нь хүлээлт багарна

### Монгол текст буруу харагдаж байна

- CSV файл сонгохдоо **UTF-8** кодчилол ашиглана
- Excel хэгээр нээхдоо `Өгөгдөл > CSV-ээс нээх > Кодчилол: UTF-8`

## 🔧 GPU идэвхжүүлэх (илүү хурдан)

CUDA суулгасан бол:

1. `mongolian_alpr.py` нээх
2. 17-р мөр: `gpu=False` → `gpu=True` хөрөв
3. Програм дахин ажилуулах

## 📞 Туслах ресурсүүд

- **OpenCV**: https://docs.opencv.org/
- **EasyOCR**: https://github.com/JaidedAI/EasyOCR
- **Tkinter**: https://docs.python.org/3/library/tkinter.html

---

✅ Бүх үе дууслаа! Идэвхүүлэхэд бэлэн!
