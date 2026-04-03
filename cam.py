# camera module controls the USB cam

import os
import cv2
import time
from datetime import datetime

from file_setup import get_today_photo_folder

CAMERA_INDEX = 1
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


class CameraManager:
    def __init__(self, index=0):
        self.index = index
        self.cap = None

    def start_camera(self):
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            print("Camera failed to open")
            return False

        time.sleep(1)  # warm-up

        # Try multiple reads (important for Pi)
        for i in range(10):
            ret, frame = self.cap.read()
            if ret:
                print("Camera initialized successfully")
                return True
            time.sleep(0.1)

        print("Camera opened but no frames received")
        return False

    def get_frame(self):
        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret:
            return None  # don't crash system

        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None

def sanitize_name(name):
    return "".join(
        c for c in name if c.isalnum() or c in (" ", "_", "-")
    ).strip().replace(" ", "_")
