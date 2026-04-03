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

        self.face_cascade = None
        self.face_cascade_path = self._find_face_cascade_path()
        if self.face_cascade_path:
            self.face_cascade = cv2.CascadeClassifier(self.face_cascade_path)

    def _find_face_cascade_path(self):
        possible_paths = [
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
            "haarcascade_frontalface_default.xml",
            os.path.join("models", "haarcascade_frontalface_default.xml"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def start_camera(self):
        if self.running:
            return True

        self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            print("[CameraManager] Failed to open camera")
            self.cap = None
            return False

        time.sleep(1.0)

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        print("[CameraManager] Camera thread started")
        return True

    def _capture_loop(self):
        while self.running:
            if self.cap is None:
                break

            ret, frame = self.cap.read()

            if ret and frame is not None:
                with self.lock:
                    self.frame = frame

            time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop_camera(self):
        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        with self.lock:
            self.frame = None

    def release(self):
        self.stop_camera()

    def detect_face(self, frame):
        if frame is None:
            return False

        if self.face_cascade is None or self.face_cascade.empty():
            # If cascade is unavailable, do not hard-fail the whole system.
            return True

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=3,
            minSize=(30, 30)
        )

        return len(faces) > 0

    def capture_image_with_face_check(self, person_name, output_folder="checkin_photos"):
        frame = self.get_frame()

        if frame is None:
            return False, None

        face_found = self.detect_face(frame)
        if not face_found:
            return False, None

        today_folder = os.path.join(output_folder, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(today_folder, exist_ok=True)

        safe_name = "".join(c for c in person_name if c.isalnum() or c in (" ", "_", "-")).strip()
        safe_name = safe_name.replace(" ", "_")

        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = "{0}_{1}.jpg".format(safe_name, timestamp)
        image_path = os.path.join(today_folder, filename)

        cv2.imwrite(image_path, frame)
        return True, image_path
