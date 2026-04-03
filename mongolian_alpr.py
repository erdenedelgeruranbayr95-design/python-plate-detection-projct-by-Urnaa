import cv2
import easyocr
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import re
from datetime import datetime
import json


class MongolianPlateRecognizer:
    def __init__(self):
        self.reader = easyocr.Reader(['en', 'mn'], gpu=False)
        self.ocr_confidence_threshold = 0.01
        self.plate_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        )
        # Mongolian plate format: NNNN TTT (4 digits + 3 letters)
        self.plate_pattern = re.compile(
            r'(?<!\d)(\d{4})[\s\-]*([\u0410-\u042F\u0401\u04E8\u04AE]{3})(?![\u0410-\u042F\u0401\u04E8\u04AE0-9])'
        )
        self.latin_to_cyrillic = str.maketrans({
            'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К',
            'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'Y': 'У',
            'a': 'А', 'b': 'В', 'c': 'С', 'e': 'Е', 'h': 'Н', 'k': 'К',
            'm': 'М', 'o': 'О', 'p': 'Р', 't': 'Т', 'x': 'Х', 'y': 'У'
        })

    def detect_plate_region(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.plate_cascade.empty():
            return []

        return self.plate_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=3,
            minSize=(45, 15),
        )

    def preprocess_plate(self, plate_img):
        plate_gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        plate_enhanced = clahe.apply(plate_gray)
        plate_denoised = cv2.fastNlMeansDenoising(plate_enhanced)
        return plate_denoised

    def _normalize_ocr_text(self, text):
        normalized = text.translate(self.latin_to_cyrillic).upper()
        normalized = re.sub(r'[^0-9\u0410-\u042F\u0401\u04E8\u04AE\s\-]', '', normalized)
        return normalized

    def is_valid_mongol_plate(self, text):
        clean_text = self._normalize_ocr_text(text)
        match = self.plate_pattern.search(clean_text)
        if not match:
            return clean_text, False
        return ''.join(match.groups()), True

    def read_plate_text(self, plate_img):
        variants = [plate_img]
        if len(plate_img.shape) == 2:
            thresh = cv2.adaptiveThreshold(
                plate_img,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                7,
            )
            variants.append(thresh)
            variants.append(cv2.bitwise_not(thresh))

        texts = []
        for variant in variants:
            results = self.reader.readtext(variant, detail=1)
            chunk_texts = []
            for (bbox, text, confidence) in results:
                if confidence < self.ocr_confidence_threshold:
                    continue
                clean_text, is_valid = self.is_valid_mongol_plate(text)
                norm_text = self._normalize_ocr_text(text)
                if norm_text:
                    left_x = min(point[0] for point in bbox)
                    chunk_texts.append((left_x, norm_text, confidence))
                if is_valid:
                    texts.append((clean_text, confidence))

            # OCR ихэвчлэн "1234" + "УБЗ" гэж салгаж уншдаг тул нийлүүлж шалгах
            if chunk_texts:
                chunk_texts.sort(key=lambda x: x[0])
                merged = ''.join(t[1] for t in chunk_texts)
                clean_text, is_valid = self.is_valid_mongol_plate(merged)
                if is_valid:
                    merged_conf = max((t[2] for t in chunk_texts), default=self.ocr_confidence_threshold)
                    texts.append((clean_text, merged_conf))

        best_by_text = {}
        for text, confidence in texts:
            best_by_text[text] = max(confidence, best_by_text.get(text, 0))
        return list(best_by_text.items())

    def process_frame(self, frame):
        detected = []
        plates = self.detect_plate_region(frame)
        candidates = [(x, y, x + w, y + h) for (x, y, w, h) in plates]

        if not candidates:
            h, w = frame.shape[:2]
            candidates.append((0, int(h * 0.35), w, int(h * 0.95)))

        for (x, y, x_end, y_end) in candidates:
            w = x_end - x
            h = y_end - y
            pad = int(max(w, h) * 0.1)
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(frame.shape[1], x_end + pad), min(frame.shape[0], y_end + pad)

            plate_img = frame[y1:y2, x1:x2]
            if plate_img.size == 0:
                continue

            plate_processed = self.preprocess_plate(plate_img)
            texts = self.read_plate_text(plate_processed)

            if texts:
                best_text, confidence = max(texts, key=lambda x: x[1])
                detected.append({
                    'text': best_text,
                    'confidence': confidence,
                    'bbox': (x1, y1, x2, y2),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'frame_timestamp': datetime.now().isoformat(),
                })

                color = (0, 255, 0) if confidence > 0.5 else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"{best_text} ({confidence:.0%})",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2,
                )

        return frame, detected


class MongolianALPRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mongolian License Plate Recognition")
        self.root.geometry("1200x750")
        self.root.configure(bg="#1e1e1e")

        self.recognizer = MongolianPlateRecognizer()
        self.cap = None
        self.running = False
        self.detected_plates = []
        self.unique_plates = {}
        self.process_every_n_frames = 3

        self._build_ui()

    def _build_ui(self):
        toolbar = tk.Frame(self.root, bg="#2c2c2c", height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        button_style = {
            'font': ('Arial', 11, 'bold'),
            'padx': 12,
            'pady': 8,
            'relief': tk.FLAT,
            'cursor': 'hand2',
        }

        tk.Button(
            toolbar,
            text="Open Video",
            command=self.open_video,
            bg="#4CAF50",
            fg="white",
            **button_style,
        ).pack(side=tk.LEFT, padx=5, pady=8)

        tk.Button(
            toolbar,
            text="Camera",
            command=self.open_camera,
            bg="#2196F3",
            fg="white",
            **button_style,
        ).pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(
            toolbar,
            text="Stop",
            command=self.stop,
            bg="#f44336",
            fg="white",
            state=tk.DISABLED,
            **button_style,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="Save CSV",
            command=self.save_csv,
            bg="#FF9800",
            fg="white",
            **button_style,
        ).pack(side=tk.RIGHT, padx=5, pady=8)

        tk.Button(
            toolbar,
            text="Save JSON",
            command=self.save_json,
            bg="#9C27B0",
            fg="white",
            **button_style,
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            toolbar,
            text="Clear",
            command=self.clear_data,
            bg="#795548",
            fg="white",
            **button_style,
        ).pack(side=tk.RIGHT, padx=5)

        main = tk.Frame(self.root, bg="#1e1e1e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left_frame = tk.Frame(main, bg="black")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Label(
            left_frame,
            bg="black",
            text="Video preview will appear here",
            fg="gray",
            font=("Arial", 16),
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(main, width=350, bg="#1e1e1e")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        right_frame.pack_propagate(False)

        header = tk.Label(
            right_frame,
            text="Detected Plates",
            bg="#1e1e1e",
            fg="#4CAF50",
            font=("Arial", 13, "bold"),
        )
        header.pack(pady=10)

        cols = ("Plate", "Confidence", "Time")
        self.tree = ttk.Treeview(right_frame, columns=cols, show="headings", height=20)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Treeview',
            background="#2c2c2c",
            foreground="white",
            fieldbackground="#2c2c2c",
            font=('Arial', 10),
        )
        style.configure(
            'Treeview.Heading',
            background="#1e1e1e",
            foreground="#4CAF50",
            font=('Arial', 10, 'bold'),
        )

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5)

        stats_frame = tk.Frame(right_frame, bg="#2c2c2c")
        stats_frame.pack(fill=tk.X, pady=10, padx=5)

        tk.Label(stats_frame, text="Total:", bg="#2c2c2c", fg="white", font=('Arial', 10)).pack(
            side=tk.LEFT
        )
        self.stat_total = tk.Label(
            stats_frame,
            text="0",
            bg="#2c2c2c",
            fg="#4CAF50",
            font=('Arial', 11, 'bold'),
        )
        self.stat_total.pack(side=tk.LEFT, padx=5)

        tk.Label(stats_frame, text="Unique:", bg="#2c2c2c", fg="white", font=('Arial', 10)).pack(
            side=tk.LEFT,
            padx=(10, 0),
        )
        self.stat_unique = tk.Label(
            stats_frame,
            text="0",
            bg="#2c2c2c",
            fg="#2196F3",
            font=('Arial', 11, 'bold'),
        )
        self.stat_unique.pack(side=tk.LEFT, padx=5)

        self.status = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status,
            bg="#333",
            fg="#4CAF50",
            anchor=tk.W,
            font=('Arial', 10),
            height=1,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def open_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv")])
        if path:
            self.start_capture(path)
            self.status.set(f"Running video: {path}")

    def open_camera(self):
        self.start_capture(0)
        self.status.set("Camera opened")

    def start_capture(self, source):
        self.stop()
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Unable to open video source!")
            return

        self.running = True
        self.btn_stop.config(state=tk.NORMAL)
        threading.Thread(target=self._processing_loop, daemon=True).start()

    def _processing_loop(self):
        frame_count = 0

        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame_count += 1
            frame_resized = cv2.resize(frame, (960, 540))
            frame_to_show = frame_resized

            if frame_count % self.process_every_n_frames == 0:
                processed, plates = self.recognizer.process_frame(frame_resized)
                frame_to_show = processed

                for plate in plates:
                    plate_text = plate['text']
                    found = False
                    for recent_text in [p['text'] for p in self.detected_plates[-20:]]:
                        if recent_text == plate_text:
                            found = True
                            break

                    if not found:
                        self.detected_plates.append(plate)
                        self.unique_plates[plate_text] = plate['time']
                        self.root.after(0, self._add_to_table, plate)
            self.root.after(0, self._update_display, frame_to_show, frame_count)

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
        self.status.set(
            f"Frame: {frame_count} | Detected: {len(self.detected_plates)} | Unique: {len(self.unique_plates)}"
        )

    def _add_to_table(self, plate):
        confidence_pct = int(plate['confidence'] * 100)
        self.tree.insert("", 0, values=(plate['text'], f"{confidence_pct}%", plate['time']))

        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[-1])

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.btn_stop.config(state=tk.DISABLED)
        self.status.set("Stopped")

    def save_csv(self):
        import pandas as pd

        if not self.detected_plates:
            messagebox.showwarning("Warning", "No detected plates yet!")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            df = pd.DataFrame(self.detected_plates)
            df.to_csv(path, index=False, encoding='utf-8-sig')
            self.status.set(f"Saved: {path}")
            messagebox.showinfo("Success", f"{len(df)} records saved")

    def save_json(self):
        if not self.detected_plates:
            messagebox.showwarning("Warning", "No detected plates yet!")
            return

        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.detected_plates, f, ensure_ascii=False, indent=2)
            self.status.set(f"Saved: {path}")
            messagebox.showinfo("Success", f"{len(self.detected_plates)} records saved")

    def clear_data(self):
        if messagebox.askyesno("Confirm", "Clear all detected data?"):
            self.detected_plates = []
            self.unique_plates = {}
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.stat_total.config(text="0")
            self.stat_unique.config(text="0")
            self.status.set("Data cleared")


if __name__ == "__main__":
    root = tk.Tk()
    app = MongolianALPRApp(root)
    root.mainloop()
