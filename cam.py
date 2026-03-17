import os
import cv2
from datetime import datetime

from file_setup import get_today_photo_folder

CAMERA_INDEX = 1


def sanitize_name(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")


def capture_image(name):
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise Exception("Could not open camera.")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise Exception("Failed to capture image.")

    photo_folder = get_today_photo_folder()
    clean_name = sanitize_name(name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "{0}_{1}.jpg".format(clean_name, timestamp)
    filepath = os.path.join(photo_folder, filename)

    cv2.imwrite(filepath, frame)
    return filepath