# Mongolian ALPR Configuration

## OCR Settings
OCR_CONFIDENCE_THRESHOLD = 0.25  # Monгол кириллийн тэлгэрүүлэх босго (25%)
OCR_MIN_TEXT_LENGTH = 7  # Дор хаяж 1234УБЗ = 7 үнэлгэ

## Plate Detection Settings
PLATE_SCALE_FACTOR = 1.1  # Haar Cascade scale
PLATE_MIN_NEIGHBORS = 5   # Cascade min detections
PLATE_MIN_SIZE = (60, 20) # Plate min width x height

## Frame Processing
SKIP_FRAMES = 2  # 2 frame тутамд 1-г боловсруулах (хурдасгалт)
MAX_TABLE_ROWS = 100  # GUI-д үзүүлэх максимум нэвтэрцүүл

## Duplicate Detection
DUPLICATE_CHECK_RANGE = 20  # Эхлэлийн N бичээсээс давхардал шалгах

## Display Settings
VIDEO_DISPLAY_WIDTH = 960
VIDEO_DISPLAY_HEIGHT = 540

## GPU Settings
USE_GPU = False  # True болговол CUDA сог ашиглана (хурдан!)
OCR_LANGUAGES = ['en', 'mn']  # Англи + Монгол

## Valid Mongolian License Plate Format
# Format: 4 digits + 3 Cyrillic letters ONLY
# Example: ✓ 1234УБЗ ✓ 5678ХОХ
# Rejected: ✗ 1234OBZ (Latin letters) ✗ ABC1234 (wrong order)
# NOTE: STRICT VALIDATION - Latin letters are COMPLETELY REJECTED
PLATE_PATTERN = r'(\d{4})\s*([А-ЯӨҮ]{3})'

## Validation Settings
STRICT_CYRILLIC_ONLY = True  # ⚠️ ONLY accept Cyrillic (А-ЯӨҮ), REJECT Latin letters completely
ALLOWED_CYRILLIC_RANGE = 'А-ЯӨҮ'  # Mongolian Cyrillic letters only

## Display Colors
COLOR_VALID_DETECTION = (0, 255, 0)      # Green - high confidence
COLOR_LOW_CONFIDENCE = (0, 165, 255)     # Orange - low confidence
COLOR_ERROR = (0, 0, 255)                # Red - error
