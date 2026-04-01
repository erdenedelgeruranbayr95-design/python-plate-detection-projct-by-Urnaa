import cv2
import easyocr
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import threading
import re
from datetime import datetime
import json

# --- Монгол дугаар таних класс (улсын өмнөх эрхэм) ---
class MongolianPlateRecognizer:
    def __init__(self):
        # EasyOCR: Англи, Монгол (Кириллийн) хэлийг дэмжих
        self.reader = easyocr.Reader(['en', 'mn'], gpu=False)
        
        # Монгол дугаарын pattern: 4 цифр + 3 Кириллийн үсэг
        # Жишээ: 1234УБЗ, 5678ХОХ гэх мэт
        self.plate_pattern = re.compile(r'(\d{4})\s*([А-ЯӨҮ]{3})', re.IGNORECASE)
    
    def detect_plate_region(self, frame):
        """Haar Cascade эсвэл YOLOv8 ашиглан дугаарын хэсгийг олох"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Орос дугаарын cascade classifier (Монголд ашиглаж болно)
        plate_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        )
        plates = plate_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 20)
        )
        return plates
    
    def preprocess_plate(self, plate_img):
        """Дугаарын сайн нэвтрүүлэхийн тулд урьдчилан боловсруулах"""
        plate_gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # Contrast оруулах
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        plate_enhanced = clahe.apply(plate_gray)
        
        # Blur арилгах
        plate_denoised = cv2.fastNlMeansDenoising(plate_enhanced)
        
        # Харилцан эргүүлэх (inverted)
        #_, plate_binary = cv2.threshold(plate_denoised, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return plate_denoised
    
    def is_valid_mongol_plate(self, text):
        """Монгол дугаарын формат эсэхийг шалгах (1234УБЗ)"""
        # Цэвэрлэх: зай, тусгаарлагч, гадны үсэг арилгах
        clean_text = re.sub(r'[^0-9А-ЯӨҮ]', '', text.upper())
        
        # Хүүхлийн үсгүүдийг Монгол кириллээр сольж өгөх
        cyrillic_map = {
            'O': 'О',  
            'P': 'Р',
            'C': 'С',
            'B': 'В',
            'A': 'А',
            'E': 'Е',
            'M': 'М',
            'H': 'Н',
            'X': 'Х',
            'K': 'К',
            'T': 'Т',
            'Y': 'У',
        }
        
        for eng, cyr in cyrillic_map.items():
            clean_text = clean_text.replace(eng, cyr)
        
        # Монгол дугаарын pattern check
        match = self.plate_pattern.search(clean_text)
        return clean_text, match is not None
    
    def read_plate_text(self, plate_img):
        """EasyOCR ашиглан дугаар унших"""
        results = self.reader.readtext(plate_img, detail=1)
        
        texts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.25:  # Монгол кириллийн хүндэр бага тул 25% хангалттай
                clean_text, is_valid = self.is_valid_mongol_plate(text)
                
                if is_valid and len(clean_text) >= 7:  # Дор хаяж 4 цифр + 3 үсэг
                    texts.append((clean_text, confidence))
        
        return texts
    
    def process_frame(self, frame):
        """Frame дотроос дугаар хайж олох"""
        detected = []
        plates = self.detect_plate_region(frame)
        
        for (x, y, w, h) in plates:
            # Padding нэмэх (10%)
            pad = int(max(w, h) * 0.1)
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(frame.shape[1], x + w + pad), min(frame.shape[0], y + h + pad)
            
            plate_img = frame[y1:y2, x1:x2]
            
            # Preprocessing
            plate_processed = self.preprocess_plate(plate_img)
            
            texts = self.read_plate_text(plate_processed)
            
            if texts:
                best_text, confidence = max(texts, key=lambda x: x[1])
                detected.append({
                    'text': best_text,
                    'confidence': confidence,
                    'bbox': (x1, y1, x2, y2),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'frame_timestamp': datetime.now().isoformat()
                })
                
                # Frame дээр зураглах
                color = (0, 255, 0) if confidence > 0.5 else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{best_text} ({confidence:.0%})",
                           (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX,
                           0.8, color, 2)
        
        return frame, detected


# --- GUI Класс (Tkinter) ---
class MongolianALPRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Монгол машины дугаар таних систем")
        self.root.geometry("1200x750")
        self.root.configure(bg="#1e1e1e")
        
        self.recognizer = MongolianPlateRecognizer()
        self.cap = None
        self.running = False
        self.detected_plates = []
        self.unique_plates = {}  # Давхардал шалгах
        
        self._build_ui()
    
    def _build_ui(self):
        # ====== Toolbar ======
        toolbar = tk.Frame(self.root, bg="#2c2c2c", height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        button_style = {
            'font': ('Arial', 11, 'bold'),
            'padx': 12,
            'pady': 8,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        tk.Button(toolbar, text="📂 Видео нээх", command=self.open_video,
                 bg="#4CAF50", fg="white", **button_style).pack(side=tk.LEFT, padx=5, pady=8)
        
        tk.Button(toolbar, text="📷 Камер", command=self.open_camera,
                 bg="#2196F3", fg="white", **button_style).pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(toolbar, text="⏹ Зогсоох",
                                  command=self.stop, bg="#f44336", fg="white",
                                  state=tk.DISABLED, **button_style)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="💾 CSV хадгалах", command=self.save_csv,
                 bg="#FF9800", fg="white", **button_style).pack(side=tk.RIGHT, padx=5, pady=8)
        
        tk.Button(toolbar, text="📊 JSON хадгалах", command=self.save_json,
                 bg="#9C27B0", fg="white", **button_style).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(toolbar, text="🗑 Цэвэрлэх", command=self.clear_data,
                 bg="#795548", fg="white", **button_style).pack(side=tk.RIGHT, padx=5)
        
        # ====== Main area ======
        main = tk.Frame(self.root, bg="#1e1e1e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # --- Video canvas (зүүн талд) ---
        left_frame = tk.Frame(main, bg="black")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Label(left_frame, bg="black", text="Видео эндэс харагдана",
                               fg="gray", font=("Arial", 16))
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # --- Results panel (баруун талд) ---
        right_frame = tk.Frame(main, width=350, bg="#1e1e1e")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        right_frame.pack_propagate(False)
        
        # === Таньсан дугаарууд ===
        header = tk.Label(right_frame, text="📋 Таньсан дугаарууд", bg="#1e1e1e",
                         fg="#4CAF50", font=("Arial", 13, "bold"))
        header.pack(pady=10)
        
        # Treeview хүснэгт
        cols = ("Дугаар", "Итгэл %", "Цаг")
        self.tree = ttk.Treeview(right_frame, columns=cols, show="headings", height=20)
        
        # Treeview styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background="#2c2c2c", foreground="white",
                       fieldbackground="#2c2c2c", font=('Arial', 10))
        style.configure('Treeview.Heading', background="#1e1e1e", foreground="#4CAF50",
                       font=('Arial', 10, 'bold'))
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # === Статистик ===
        stats_frame = tk.Frame(right_frame, bg="#2c2c2c")
        stats_frame.pack(fill=tk.X, pady=10, padx=5)
        
        tk.Label(stats_frame, text="Нийт таньсан:", bg="#2c2c2c", fg="white",
                font=('Arial', 10)).pack(side=tk.LEFT)
        self.stat_total = tk.Label(stats_frame, text="0", bg="#2c2c2c", fg="#4CAF50",
                                   font=('Arial', 11, 'bold'))
        self.stat_total.pack(side=tk.LEFT, padx=5)
        
        tk.Label(stats_frame, text="Өнөөдөр таньсан:", bg="#2c2c2c", fg="white",
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.stat_unique = tk.Label(stats_frame, text="0", bg="#2c2c2c", fg="#2196F3",
                                    font=('Arial', 11, 'bold'))
        self.stat_unique.pack(side=tk.LEFT, padx=5)
        
        # ====== Status bar ======
        self.status = tk.StringVar(value="✓ Бэлэн байна...")
        status_bar = tk.Label(self.root, textvariable=self.status, bg="#333",
                             fg="#4CAF50", anchor=tk.W, font=('Arial', 10), height=1)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def open_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Видео файл", "*.mp4 *.avi *.mov *.mkv *.flv")]
        )
        if path:
            self.start_capture(path)
            self.status.set(f"▶ Видео эхлэв: {path}")
    
    def open_camera(self):
        self.start_capture(0)
        self.status.set("▶ Камер нээгдэв")
    
    def start_capture(self, source):
        self.stop()
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            messagebox.showerror("Алдаа", "Видео открыть үл боломжтой!")
            return
        
        self.running = True
        self.btn_stop.config(state=tk.NORMAL)
        threading.Thread(target=self._processing_loop, daemon=True).start()
    
    def _processing_loop(self):
        frame_count = 0
        fps_start = datetime.now()
        
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Хурдасгалт: 2 frame тутамд (улирал) 1-г л боловсруулах
            if frame_count % 2 == 0:
                frame_resized = cv2.resize(frame, (960, 540))
                processed, plates = self.recognizer.process_frame(frame_resized)
                
                for plate in plates:
                    plate_text = plate['text']
                    
                    # Давхардал шалгах (сүүлийн 20 записей дундуур)
                    found = False
                    for recent_text in [p['text'] for p in self.detected_plates[-20:]]:
                        if recent_text == plate_text:
                            found = True
                            break
                    
                    if not found:
                        self.detected_plates.append(plate)
                        self.unique_plates[plate_text] = plate['time']
                        self.root.after(0, self._add_to_table, plate)
                
                self.root.after(0, self._update_display, processed, frame_count)
        
        self.root.after(0, self.stop)
    
    def _update_display(self, frame, frame_count):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail((900, 540))
        photo = ImageTk.PhotoImage(img)
        
        self.canvas.config(image=photo, text="")
        self.canvas.image = photo
        
        self.stat_total.config(text=str(len(self.detected_plates)))
        self.stat_unique.config(text=str(len(self.unique_plates)))
        self.status.set(f"▶ Frame: {frame_count} | Таньсан: {len(self.detected_plates)} | Өнөөд: {len(self.unique_plates)}")
    
    def _add_to_table(self, plate):
        confidence_pct = int(plate['confidence'] * 100)
        self.tree.insert("", 0, values=(
            plate['text'],
            f"{confidence_pct}%",
            plate['time']
        ))
        
        # Max 100 бичээс (performance)
        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[-1])
    
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.btn_stop.config(state=tk.DISABLED)
        self.status.set("⏹ Зогссон.")
    
    def save_csv(self):
        import pandas as pd
        if not self.detected_plates:
            messagebox.showwarning("Сүүл", "Таньсан дугаар байхгүй!")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                          filetypes=[("CSV файл", "*.csv")])
        if path:
            df = pd.DataFrame(self.detected_plates)
            df.to_csv(path, index=False, encoding='utf-8-sig')
            self.status.set(f"✓ Хадгалагдлаа: {path}")
            messagebox.showinfo("Амжилттай", f"{len(df)} бичээс хадгалагдлаа")
    
    def save_json(self):
        if not self.detected_plates:
            messagebox.showwarning("Сүүл", "Таньсан дугаар байхгүй!")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                          filetypes=[("JSON файл", "*.json")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.detected_plates, f, ensure_ascii=False, indent=2)
            self.status.set(f"✓ Хадгалагдлаа: {path}")
            messagebox.showinfo("Амжилттай", f"{len(self.detected_plates)} бичээс хадгалагдлаа")
    
    def clear_data(self):
        if messagebox.askyesno("Баталгаажуулах", "Бүх өгөгдөл цэвэрлэгдэх үү?"):
            self.detected_plates = []
            self.unique_plates = {}
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.stat_total.config(text="0")
            self.stat_unique.config(text="0")
            self.status.set("✓ Өгөгдөл цэвэрлэгдлээ")


# ====== Эхлүүлэх ======
if __name__ == "__main__":
    root = tk.Tk()
    app = MongolianALPRApp(root)
    root.mainloop()
