import math
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

import cv2


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


@dataclass
class FrameMetrics:
    total_score: float
    acceptable: bool
    used_face_detection: bool
    face_count: int
    centered_score: float
    size_score: float
    edge_score: float
    sharpness_score: float
    brightness_score: float
    heuristic_score: float


@dataclass
class CaptureResult:
    frame: Any
    metrics: Optional[FrameMetrics]
    used_session_candidate: bool


class BestFrameScorer:
    def __init__(self, sample_width=320):
        self.sample_width = sample_width
        self.face_cascade = self._load_face_cascade()

    def _load_face_cascade(self):
        try:
            cascade_path = os.path.join(
                cv2.data.haarcascades,
                "haarcascade_frontalface_default.xml"
            )
            cascade = cv2.CascadeClassifier(cascade_path)
            if cascade.empty():
                return None
            return cascade
        except Exception:
            return None

    def evaluate(self, frame):
        if frame is None:
            return None

        working_frame = self._downscale(frame)
        gray = cv2.cvtColor(working_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self._detect_faces(gray)

        if faces:
            return self._score_with_faces(gray, faces)

        return self._score_without_faces(gray)

    def _downscale(self, frame):
        height, width = frame.shape[:2]
        if width <= self.sample_width:
            return frame

        scale = self.sample_width / float(width)
        resized_height = max(1, int(height * scale))
        return cv2.resize(
            frame,
            (self.sample_width, resized_height),
            interpolation=cv2.INTER_AREA
        )

    def _detect_faces(self, gray_frame):
        if self.face_cascade is None:
            return []

        min_face = max(28, int(min(gray_frame.shape[:2]) * 0.12))
        try:
            faces = self.face_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.15,
                minNeighbors=4,
                minSize=(min_face, min_face)
            )
        except Exception:
            return []

        return list(faces) if len(faces) else []

    def _score_with_faces(self, gray_frame, faces):
        frame_height, frame_width = gray_frame.shape[:2]
        frame_area = float(frame_height * frame_width)
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x_pos, y_pos, width, height = largest_face
        face_area = float(width * height)
        face_ratio = face_area / frame_area if frame_area else 0.0

        face_crop = gray_frame[y_pos:y_pos + height, x_pos:x_pos + width]
        centered_score = self._centered_score(frame_width, frame_height, x_pos, y_pos, width, height)
        size_score = self._size_score(face_ratio)
        edge_score = self._edge_score(frame_width, frame_height, x_pos, y_pos, width, height)
        sharpness_score = self._sharpness_score(face_crop)
        brightness_score = self._brightness_score(face_crop)
        dominant_score = self._dominant_face_score(faces)

        total_score = (
            0.30 +
            0.18 * centered_score +
            0.15 * size_score +
            0.10 * edge_score +
            0.14 * sharpness_score +
            0.08 * brightness_score +
            0.05 * dominant_score
        )

        if len(faces) > 1:
            total_score -= 0.08

        acceptable = (
            total_score >= 0.55 and
            face_ratio >= 0.04 and
            edge_score >= 0.10 and
            sharpness_score >= 0.10
        )

        return FrameMetrics(
            total_score=_clamp(total_score),
            acceptable=acceptable,
            used_face_detection=True,
            face_count=len(faces),
            centered_score=centered_score,
            size_score=size_score,
            edge_score=edge_score,
            sharpness_score=sharpness_score,
            brightness_score=brightness_score,
            heuristic_score=0.0
        )

    def _score_without_faces(self, gray_frame):
        sharpness_score = self._sharpness_score(gray_frame)
        brightness_score = self._brightness_score(gray_frame)
        contrast_score = self._contrast_score(gray_frame)

        total_score = (
            0.20 +
            0.40 * sharpness_score +
            0.25 * brightness_score +
            0.15 * contrast_score
        )

        acceptable = (
            total_score >= 0.48 and
            sharpness_score >= 0.12 and
            brightness_score >= 0.12
        )

        return FrameMetrics(
            total_score=_clamp(total_score),
            acceptable=acceptable,
            used_face_detection=False,
            face_count=0,
            centered_score=0.0,
            size_score=0.0,
            edge_score=0.0,
            sharpness_score=sharpness_score,
            brightness_score=brightness_score,
            heuristic_score=contrast_score
        )

    def _centered_score(self, frame_width, frame_height, x_pos, y_pos, width, height):
        face_center_x = x_pos + (width / 2.0)
        face_center_y = y_pos + (height / 2.0)
        frame_center_x = frame_width / 2.0
        frame_center_y = frame_height / 2.0
        distance = math.hypot(face_center_x - frame_center_x, face_center_y - frame_center_y)
        max_distance = math.hypot(frame_center_x, frame_center_y) or 1.0
        return _clamp(1.0 - (distance / max_distance))

    def _size_score(self, face_ratio):
        if 0.08 <= face_ratio <= 0.32:
            return 1.0
        if face_ratio < 0.08:
            return _clamp(face_ratio / 0.08)
        return _clamp(1.0 - ((face_ratio - 0.32) / 0.32))

    def _edge_score(self, frame_width, frame_height, x_pos, y_pos, width, height):
        min_margin = min(
            x_pos,
            y_pos,
            max(0, frame_width - (x_pos + width)),
            max(0, frame_height - (y_pos + height))
        )
        target_margin = min(frame_width, frame_height) * 0.08
        if target_margin <= 0:
            return 0.0
        return _clamp(min_margin / target_margin)

    def _dominant_face_score(self, faces):
        if len(faces) == 1:
            return 1.0

        areas = sorted((face[2] * face[3] for face in faces), reverse=True)
        total_area = float(sum(areas)) or 1.0
        return _clamp(areas[0] / total_area)

    def _sharpness_score(self, gray_frame):
        if gray_frame.size == 0:
            return 0.0

        variance = cv2.Laplacian(gray_frame, cv2.CV_64F).var()
        return _clamp(variance / 140.0)

    def _brightness_score(self, gray_frame):
        if gray_frame.size == 0:
            return 0.0

        brightness = float(gray_frame.mean()) / 255.0
        return _clamp(1.0 - (abs(brightness - 0.55) / 0.35))

    def _contrast_score(self, gray_frame):
        if gray_frame.size == 0:
            return 0.0

        contrast = float(gray_frame.std())
        return _clamp(contrast / 64.0)


class CaptureSession:
    def __init__(self, camera_manager, scorer, sample_interval=0.2, duration=None):
        self.camera_manager = camera_manager
        self.scorer = scorer
        self.sample_interval = sample_interval
        self.duration = duration
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.best_frame = None
        self.best_metrics = None
        self.samples_seen = 0

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        deadline = None
        if self.duration is not None:
            deadline = time.monotonic() + self.duration

        while not self.stop_event.is_set():
            if deadline is not None and time.monotonic() >= deadline:
                break

            frame = self.camera_manager.get_frame()
            if frame is not None:
                metrics = self.scorer.evaluate(frame)
                if metrics is not None:
                    with self.lock:
                        self.samples_seen += 1
                        if self._is_better_candidate(metrics):
                            self.best_frame = frame.copy()
                            self.best_metrics = metrics

            self.stop_event.wait(self.sample_interval)

    def _is_better_candidate(self, metrics):
        if self.best_metrics is None:
            return True

        if metrics.acceptable != self.best_metrics.acceptable:
            return metrics.acceptable

        return metrics.total_score > self.best_metrics.total_score

    def wait(self):
        if self.thread:
            self.thread.join()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=max(1.0, self.sample_interval * 4))

    def snapshot_result(self):
        with self.lock:
            frame = self.best_frame.copy() if self.best_frame is not None else None
            return CaptureResult(
                frame=frame,
                metrics=self.best_metrics,
                used_session_candidate=frame is not None
            )


class CaptureService:
    KNOWN_USER_DURATION = 1.2
    SAMPLE_INTERVAL = 0.2

    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
        self.scorer = BestFrameScorer()
        self.enrollment_session = None
        self.enrollment_lock = threading.Lock()

    def start_camera(self):
        return self.camera_manager.start_camera()

    def stop_camera(self):
        self.cancel_enrollment_session()
        self.camera_manager.release()

    def is_camera_running(self):
        return self.camera_manager.running

    def capture_known_user(self, person_name):
        if not self.start_camera():
            return False, None, None

        session = CaptureSession(
            self.camera_manager,
            self.scorer,
            sample_interval=self.SAMPLE_INTERVAL,
            duration=self.KNOWN_USER_DURATION
        )
        session.start()
        session.wait()
        result = session.snapshot_result()

        if result.frame is not None and result.metrics and result.metrics.acceptable:
            success, path = self.camera_manager.save_frame(person_name, result.frame)
            if success:
                return True, path, result.metrics

        success, path = self.camera_manager.capture_image_with_face_check(person_name)
        return success, path, result.metrics

    def start_enrollment_session(self):
        if not self.start_camera():
            return False

        with self.enrollment_lock:
            self._stop_enrollment_session_locked()
            session = CaptureSession(
                self.camera_manager,
                self.scorer,
                sample_interval=self.SAMPLE_INTERVAL
            )
            session.start()
            self.enrollment_session = session
            return True

    def finalize_enrollment_capture(self, person_name):
        with self.enrollment_lock:
            session = self.enrollment_session
            self.enrollment_session = None

        if session:
            session.stop()
            result = session.snapshot_result()
            if result.frame is not None and result.metrics and result.metrics.acceptable:
                success, path = self.camera_manager.save_frame(person_name, result.frame)
                if success:
                    return True, path, result.metrics

            fallback_metrics = result.metrics
        else:
            fallback_metrics = None

        success, path = self.camera_manager.capture_image_with_face_check(person_name)
        return success, path, fallback_metrics

    def cancel_enrollment_session(self):
        with self.enrollment_lock:
            self._stop_enrollment_session_locked()

    def _stop_enrollment_session_locked(self):
        if self.enrollment_session:
            self.enrollment_session.stop()
            self.enrollment_session = None
