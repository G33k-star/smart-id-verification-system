import os
import re
import threading
import time
from datetime import datetime

import cv2

from config import (
    CAMERA_DISCOVERY_RETRY_SEC,
    CAMERA_INDEX_MAX,
    CAMERA_INDEX_MIN,
    CAMERA_PROBE_ATTEMPTS,
    CAMERA_PROBE_READ_INTERVAL_SEC,
    CAMERA_PROBE_WARMUP_SEC,
    CAMERA_READ_FAILURE_LIMIT,
    DATA_PHOTOS_CHECKINS_FOLDER,
)


class CameraManager:
    CAPTURE_LOOP_SLEEP_SEC = 0.01
    DISCOVERY_IDLE_SEC = 0.25

    def __init__(self):
        self.cap = None
        self.active_index = None
        self.running = False
        self.frame = None

        self.lock = threading.RLock()
        self.capture_thread = None
        self.discovery_thread = None
        self.shutdown_event = threading.Event()
        self.discovery_wake_event = threading.Event()

        self.state_callback = None
        self.last_reported_available = False

    def set_state_callback(self, callback):
        self.state_callback = callback

    def start_camera(self):
        self._ensure_discovery_thread()
        self.discovery_wake_event.set()
        return self.running

    def _ensure_discovery_thread(self):
        if self.discovery_thread and self.discovery_thread.is_alive():
            return

        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            daemon=True
        )
        self.discovery_thread.start()

    def _discovery_loop(self):
        print("[CameraManager] Discovery thread started")

        while not self.shutdown_event.is_set():
            if self.running:
                self.discovery_wake_event.wait(self.DISCOVERY_IDLE_SEC)
                self.discovery_wake_event.clear()
                continue

            if self._discover_camera_once():
                self.discovery_wake_event.clear()
                continue

            self.discovery_wake_event.wait(CAMERA_DISCOVERY_RETRY_SEC)
            self.discovery_wake_event.clear()

        print("[CameraManager] Discovery thread stopped")

    def _discover_camera_once(self):
        for index in range(CAMERA_INDEX_MIN, CAMERA_INDEX_MAX + 1):
            if self.shutdown_event.is_set() or self.running:
                return self.running

            if self._probe_index(index):
                return True

        return False

    def _probe_index(self, index):
        cap = None
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if not cap.isOpened():
                return False

            if CAMERA_PROBE_WARMUP_SEC > 0:
                time.sleep(CAMERA_PROBE_WARMUP_SEC)

            first_frame = None
            attempts = max(1, CAMERA_PROBE_ATTEMPTS)
            for attempt in range(attempts):
                ret, frame = cap.read()
                if ret and frame is not None and getattr(frame, "size", 0) > 0:
                    first_frame = frame
                    break

                if attempt < attempts - 1:
                    time.sleep(CAMERA_PROBE_READ_INTERVAL_SEC)

            if first_frame is None:
                return False

            self._activate_camera(index, cap, first_frame)
            cap = None
            return True
        except Exception as exc:
            print("[CameraManager] Probe failed for index {0}: {1}".format(index, exc))
            return False
        finally:
            if cap is not None:
                cap.release()

    def _activate_camera(self, index, cap, first_frame):
        with self.lock:
            if self.shutdown_event.is_set():
                cap.release()
                return

            self.cap = cap
            self.active_index = index
            self.frame = first_frame.copy()
            self.running = True

            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()

        print("[CameraManager] Camera connected")
        self._notify_state_change(True)

    def _capture_loop(self):
        failure_count = 0

        while not self.shutdown_event.is_set():
            with self.lock:
                cap = self.cap

            if cap is None or not self.running:
                break

            ret, frame = cap.read()
            if ret and frame is not None and getattr(frame, "size", 0) > 0:
                failure_count = 0
                with self.lock:
                    if cap is self.cap:
                        self.frame = frame
            else:
                failure_count += 1
                if failure_count >= CAMERA_READ_FAILURE_LIMIT:
                    print("[CameraManager] Camera stream lost")
                    self._deactivate_camera(cap, notify=True)
                    break

            time.sleep(self.CAPTURE_LOOP_SLEEP_SEC)

    def _deactivate_camera(self, expected_cap=None, notify=False):
        with self.lock:
            if expected_cap is not None and self.cap is not expected_cap:
                return

            cap = self.cap
            self.cap = None
            self.active_index = None
            self.running = False
            self.frame = None
            self.capture_thread = None

        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass

        if notify:
            print("[CameraManager] Camera unavailable")
            self._notify_state_change(False)
            self.discovery_wake_event.set()

    def _notify_state_change(self, available):
        if self.last_reported_available == available:
            return

        self.last_reported_available = available
        callback = self.state_callback
        if callback is None:
            return

        try:
            callback(available)
        except Exception as exc:
            print("[CameraManager] State callback failed:", exc)

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
        self.shutdown_event.set()
        self.discovery_wake_event.set()

        self._deactivate_camera(notify=False)

        capture_thread = self.capture_thread
        if capture_thread and capture_thread.is_alive():
            capture_thread.join(timeout=1)

        discovery_thread = self.discovery_thread
        if discovery_thread and discovery_thread.is_alive():
            discovery_thread.join(timeout=1)

        self.discovery_thread = None
        self.capture_thread = None

    def capture_image(self, person_name, output_folder=None, identity_value=None):
        frame = self.get_frame()
        return self.save_frame(person_name, frame, output_folder, identity_value)
