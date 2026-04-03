import cv2
import time


class CameraManager:
    def __init__(self, index=0):
        self.index = index
        self.cap = None
        self.is_running = False

    def start_camera(self):
        """
        Initialize camera safely.
        Returns True if usable, False otherwise.
        """

        # Open camera (force V4L2 backend for Pi stability)
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            print("[CameraManager] Camera failed to open")
            self.cap = None
            return False  # <-- Option C (no UI call here)

        # Warm-up period (critical on Pi)
        time.sleep(1)

        # Try multiple reads (avoid false failure)
        for i in range(10):
            ret, frame = self.cap.read()
            print(f"[CameraManager] Warmup attempt {i}: ret={ret}")

            if ret and frame is not None:
                self.is_running = True
                print("[CameraManager] Camera initialized successfully")
                return True

            time.sleep(0.1)

        # If we reach here → camera opened but unusable
        print("[CameraManager] Camera opened but no frames received")
        self.cap.release()
        self.cap = None
        return False

    def get_frame(self):
        """
        Safely get a frame.
        Returns None if frame not available (do NOT treat as fatal).
        """

        if not self.cap or not self.is_running:
            return None

        ret, frame = self.cap.read()

        if not ret or frame is None:
            # Non-fatal: skip frame
            return None

        return frame

    def release(self):
        """
        Release camera cleanly.
        """

        if self.cap:
            print("[CameraManager] Releasing camera")
            self.cap.release()
            self.cap = None

        self.is_running = False
