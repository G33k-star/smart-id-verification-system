import os
import re
import cv2
import threading
import time
from datetime import datetime
from config import DATA_PHOTOS_CHECKINS_FOLDER


class CameraManager:
    def __init__(self, index=0):
        self.index = index
        self.cap = None
        self.running = False
        self.frame = None
        self.lock = threading.Lock()
        self.thread = None

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

    def _sanitize_photo_part(self, value):
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
        cleaned = cleaned.strip("._-")
        return cleaned or "unknown"

    def _build_photo_stem(self, person_name, identity_value=None):
        safe_name = self._sanitize_photo_part(person_name)
        if identity_value:
            safe_identity = self._sanitize_photo_part(identity_value)
            return f"{safe_name}-{safe_identity}"
        return safe_name

    def _get_today_photo_folder(self, output_folder=None):
        output_folder = output_folder or DATA_PHOTOS_CHECKINS_FOLDER
        return os.path.join(output_folder, datetime.now().strftime("%Y-%m-%d"))

    def find_saved_photo_for_today(self, person_name, identity_value=None, output_folder=None):
        today_folder = self._get_today_photo_folder(output_folder)
        if not os.path.isdir(today_folder):
            return None

        prefix = self._build_photo_stem(person_name, identity_value) + "_"
        for filename in sorted(os.listdir(today_folder)):
            if filename.startswith(prefix) and filename.lower().endswith(".jpg"):
                return os.path.join(today_folder, filename)

        return None

    def save_frame(self, person_name, frame, output_folder=None, identity_value=None):
        if frame is None:
            return False, None

        today_folder = self._get_today_photo_folder(output_folder)
        os.makedirs(today_folder, exist_ok=True)

        photo_stem = self._build_photo_stem(person_name, identity_value)
        filename = f"{photo_stem}_{datetime.now().strftime('%H-%M-%S')}.jpg"
        path = os.path.join(today_folder, filename)

        if not cv2.imwrite(path, frame):
            return False, None

        return True, path

    def release(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=1)

        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_image(self, person_name, output_folder=None, identity_value=None):
        frame = self.get_frame()
        return self.save_frame(person_name, frame, output_folder, identity_value)
