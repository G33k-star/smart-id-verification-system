import cv2
import threading
import time


class CameraManager:
    def __init__(self, index=0):
        self.index = index
        self.cap = None
        self.running = False
        self.frame = None
        self.lock = threading.Lock()

    def start_camera(self):
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            print("[CameraManager] Failed to open camera")
            return False

        self.running = True

        # Start background thread
        thread = threading.Thread(target=self._capture_loop, daemon=True)
        thread.start()

        print("[CameraManager] Camera thread started")
        return True

    def _capture_loop(self):
        time.sleep(1)  # warm-up

        while self.running:
            ret, frame = self.cap.read()

            if ret:
                with self.lock:
                    self.frame = frame

            time.sleep(0.01)  # small delay prevents CPU overload

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def release(self):
        self.running = False

        if self.cap:
            self.cap.release()
            self.cap = None
