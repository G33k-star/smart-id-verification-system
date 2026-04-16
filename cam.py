import os
import cv2
import threading
import time
from datetime import datetime
from config import PHOTO_FOLDER


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

    def release(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=1)

        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_image_with_face_check(self, person_name, output_folder=None):
        frame = self.get_frame()

        if frame is None:
            return False, None

        output_folder = output_folder or PHOTO_FOLDER
        today_folder = os.path.join(output_folder, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(today_folder, exist_ok=True)

        safe_name = person_name.replace(" ", "_")
        filename = f"{safe_name}_{datetime.now().strftime('%H-%M-%S')}.jpg"
        path = os.path.join(today_folder, filename)

        cv2.imwrite(path, frame)
        return True, path
