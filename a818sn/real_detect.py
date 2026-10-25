# A818SN - REAL Detection with YOLO + Webcam
import cv2
import time
from ultralytics import YOLO
from collections import deque

class RealTracker:
    def __init__(self, model_path='yolov8n.pt', max_len=200):
        self.model = YOLO(model_path)
        self.cap = cv2.VideoCapture(0)
        self.x = deque(maxlen=max_len)
        self.y = deque(maxlen=max_len)
        self.t = deque(maxlen=max_len)
        self.track_id = 1
        self.step = 0
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

    def get_frame_with_detections(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        self.step += 1
        self.frame_count += 1

        results = self.model.predict(frame, verbose=False, conf=0.25)

        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            detections.append({
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'conf': conf,
                'cls': cls
            })

        annotated = results[0].plot()

        if detections:
            d = detections[0]
            cx = (d['bbox'][0] + d['bbox'][2]) / 2
            cy = (d['bbox'][1] + d['bbox'][3]) / 2
            self.x.append(cx)
            self.y.append(cy)
            self.t.append(self.step)

        elapsed = time.time() - self.start_time
        if elapsed > 0:
            self.fps = self.frame_count / elapsed

        return annotated, detections

    def release(self):
        self.cap.release()

    def reset(self):
        self.x.clear()
        self.y.clear()
        self.t.clear()
        self.step = 0
        self.frame_count = 0
        self.start_time = time.time()