import os
import cv2
import threading
import time
from datetime import datetime


class CameraManager:
    def __init__(self, index=0):
        self.index = index
        self.cap = None
        self.running = False
        self.frame = None
        self.lock = threading.Lock()
        self.thread = None

        # Try to load face cascade (optional)
        self.face_cascade = None
        cascade_path = self._find_cascade()

        if cascade_path:
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            print(f"[CameraManager] Loaded cascade: {cascade_path}")
        else:
            print("[CameraManager] No cascade found (face detection disabled)")

    def _find_cascade(self):
        paths = [
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
            "haarcascade_frontalface_default.xml",
            os.path.join("models", "haarcascade_frontalface_default.xml"),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def start_camera(self):
        if self.running:
            return True

        self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            print("[CameraManager] Failed to open camera")
            self.cap = None
            return False

        time.sleep(1)

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        print("[CameraManager] Camera thread started")
        return True

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop_camera(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

        if self.cap:
            self.cap.release()
            self.cap = None

    def release(self):
        self.stop_camera()

    # =========================
    # FACE DETECTION (NON-BLOCKING)
    # =========================
    def detect_face(self, frame):
        if self.face_cascade is None:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=3,
            minSize=(30, 30)
        )

        return len(faces) > 0

    # =========================
    # IMAGE CAPTURE (ALWAYS SUCCEEDS)
    # =========================
    def capture_image_with_face_check(self, person_name, output_folder="checkin_photos"):
        frame = self.get_frame()

        if frame is None:
            return False, None

        # Try face detection (DO NOT BLOCK)
        face_found = self.detect_face(frame)
        if not face_found:
            print("[CameraManager] WARNING: No face detected (continuing)")

        today_folder = os.path.join(output_folder, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(today_folder, exist_ok=True)

        safe_name = "".join(c for c in person_name if c.isalnum() or c in (" ", "_", "-"))
        safe_name = safe_name.replace(" ", "_")

        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = f"{safe_name}_{timestamp}.jpg"
        path = os.path.join(today_folder, filename)

        cv2.imwrite(path, frame)

        return True, path
