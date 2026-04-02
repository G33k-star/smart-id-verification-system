# camera module controls the USB cam

import os
import cv2
from datetime import datetime

from file_setup import get_today_photo_folder

CAMERA_INDEX = 1
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


class CameraManager:
    def __init__(self, camera_index=CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)

        if self.face_cascade.empty():
            raise Exception("Could not load Haar cascade.")

    def start(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise Exception("Could not open camera.")

        # Warm-up frames
        for _ in range(10):
            self.cap.read()

    def stop(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def is_running(self):
        return self.cap is not None and self.cap.isOpened()

    def get_frame(self):
        if not self.is_running():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )

        return faces

    def get_preview_frame(self):
        frame = self.get_frame()
        if frame is None:
            return None, []

        faces = self.detect_faces(frame)

        preview = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return preview, faces

    def capture_image_with_face_check(self, name):
        if not self.is_running():
            self.start()

        frame = self.get_frame()
        if frame is None:
            # Try a few more frames in case the camera is warming up
            for _ in range(10):
                frame = self.get_frame()
                if frame is not None:
                    break

        if frame is None:
            raise Exception("Failed to capture image.")

        faces = self.detect_faces(frame)

        if len(faces) == 0:
            return False, None

        folder = get_today_photo_folder()
        clean_name = sanitize_name(name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{clean_name}_{timestamp}.jpg"
        filepath = os.path.join(folder, filename)

        cv2.imwrite(filepath, frame)
        return True, filepath


def sanitize_name(name):
    return "".join(
        c for c in name if c.isalnum() or c in (" ", "_", "-")
    ).strip().replace(" ", "_")
