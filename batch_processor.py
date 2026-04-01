"""
Batch processing script for license plate detection
Камер эсвэл видео файлаас дугаарыг олж CSV-д хүүхлэх скрипт
"""

import cv2
import easyocr
import re
from datetime import datetime
import argparse
import sys

class SimpleMongolianALPR:
    def __init__(self, use_gpu=False):
        print("[INFO] EasyOCR загаршучилж байна...")
        self.reader = easyocr.Reader(['en', 'mn'], gpu=use_gpu)
        self.plate_pattern = re.compile(r'(\d{4})\s*([А-ЯӨҮ]{3})', re.IGNORECASE)
    
    def detect_plate_region(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        plate_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        )
        plates = plate_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 20)
        )
        return plates
    
    def preprocess_plate(self, plate_img):
        plate_gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        plate_enhanced = clahe.apply(plate_gray)
        plate_denoised = cv2.fastNlMeansDenoising(plate_enhanced)
        return plate_denoised
    
    def is_valid_mongol_plate(self, text):
        clean_text = re.sub(r'[^0-9А-ЯӨҮ]', '', text.upper())
        
        cyrillic_map = {
            'O': 'О', 'P': 'Р', 'C': 'С', 'B': 'В', 'A': 'А',
            'E': 'Е', 'M': 'М', 'H': 'Н', 'X': 'Х', 'K': 'К',
            'T': 'Т', 'Y': 'У'
        }
        
        for eng, cyr in cyrillic_map.items():
            clean_text = clean_text.replace(eng, cyr)
        
        match = self.plate_pattern.search(clean_text)
        return clean_text, match is not None
    
    def read_plate_text(self, plate_img):
        results = self.reader.readtext(plate_img, detail=1)
        
        texts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.25:
                clean_text, is_valid = self.is_valid_mongol_plate(text)
                if is_valid and len(clean_text) >= 7:
                    texts.append((clean_text, confidence))
        
        return texts
    
    def process_frame(self, frame):
        detected = []
        plates = self.detect_plate_region(frame)
        
        for (x, y, w, h) in plates:
            pad = int(max(w, h) * 0.1)
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(frame.shape[1], x + w + pad), min(frame.shape[0], y + h + pad)
            
            plate_img = frame[y1:y2, x1:x2]
            plate_processed = self.preprocess_plate(plate_img)
            texts = self.read_plate_text(plate_processed)
            
            if texts:
                best_text, confidence = max(texts, key=lambda x: x[1])
                detected.append({
                    'text': best_text,
                    'confidence': confidence,
                    'time': datetime.now().strftime('%H:%M:%S')
                })
        
        return detected
    
    def process_video(self, video_path, output_csv=None, skip_frames=2):
        """Видео файлаас дугаарыг цуб олох"""
        print(f"[INFO] Видео нээж байна: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("[ERROR] Видео нээхэд амжилтгүй!")
            return None
        
        all_detections = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count % skip_frames == 0:
                frame_resized = cv2.resize(frame, (960, 540))
                detections = self.process_frame(frame_resized)
                
                for det in detections:
                    print(f"[FOUND] Frame {frame_count}: {det['text']} (confidence: {det['confidence']:.0%})")
                    all_detections.append({
                        'frame': frame_count,
                        'plate': det['text'],
                        'confidence': f"{det['confidence']:.2%}",
                        'time': det['time']
                    })
        
        cap.release()
        print(f"[INFO] Боловсруулалт дууслаа. Нийт {len(all_detections)} дугаар таньсан.")
        
        if output_csv and all_detections:
            import pandas as pd
            df = pd.DataFrame(all_detections)
            df.to_csv(output_csv, index=False, encoding='utf-8-sig')
            print(f"[SUCCESS] CSV хадгалагдлаа: {output_csv}")
        
        return all_detections


def main():
    parser = argparse.ArgumentParser(description="Монгол машины дугаар таних (Batch)")
    parser.add_argument('-i', '--input', type=str, help='Видео файлын яваа эсвэл камер (0)')
    parser.add_argument('-o', '--output', type=str, help='CSV гаралтын файл')
    parser.add_argument('--skip', type=int, default=2, help='Frame skip хэмжээ (2)')
    parser.add_argument('--gpu', action='store_true', help='GPU ашиглах')
    
    args = parser.parse_args()
    
    if not args.input:
        print("Usage: python batch_processor.py -i video.mp4 -o results.csv")
        print("       python batch_processor.py -i 0 -o camera.csv  (камер)")
        return
    
    recognizer = SimpleMongolianALPR(use_gpu=args.gpu)
    
    # Камер эсвэл видео файл?
    if args.input == '0':
        print("[INFO] Камер нээж байна...")
        source = 0
    else:
        source = args.input
    
    detections = recognizer.process_video(source, output_csv=args.output, skip_frames=args.skip)


if __name__ == "__main__":
    main()
