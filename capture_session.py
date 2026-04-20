import math
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

import cv2

from config import (
    BLUR_THRESHOLD,
    BRIGHTNESS_MAX,
    BRIGHTNESS_MIN,
    BUFFER_DURATION_SEC,
    CENTER_TOLERANCE_RATIO,
    CLEAR_FACE_CENTER_SCORE,
    CLEAR_FACE_EDGE_SCORE,
    DATA_PHOTOS_FOLDER,
    DEBUG_SAVE_FRAMES,
    FACE_DETECT_SCALE,
    FRAME_SAMPLE_INTERVAL_MS,
    MAX_BUFFER_FRAMES,
    MIN_FACE_SIZE_RATIO,
    POST_EVENT_WINDOW_SEC,
    PREFERRED_POST_EVENT_SEC,
    PRE_EVENT_WINDOW_SEC,
)


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
    face_ratio: float
    single_clear_face: bool
    blur_variance: float
    brightness_value: float


@dataclass
class BufferedFrame:
    timestamp: float
    frame: Any
    metrics: FrameMetrics


@dataclass
class CaptureResult:
    frame: Any
    metrics: Optional[FrameMetrics]
    used_event_candidate: bool


class EventCapture:
    POLL_INTERVAL_SEC = 0.05

    def __init__(self, capture_service, event_time):
        self.capture_service = capture_service
        self.event_time = event_time
        self.ready_at = event_time + POST_EVENT_WINDOW_SEC
        self.cancel_event = threading.Event()
        self.completed_event = threading.Event()
        self.result = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while not self.cancel_event.is_set():
            remaining = self.ready_at - time.monotonic()
            if remaining <= 0:
                break
            self.cancel_event.wait(min(self.POLL_INTERVAL_SEC, remaining))

        if not self.cancel_event.is_set():
            self.result = self.capture_service.select_event_result(self.event_time)

        self.completed_event.set()

    def wait(self, timeout=None):
        self.completed_event.wait(timeout)
        return self.result

    def cancel(self):
        self.cancel_event.set()


class BestFrameScorer:
    def __init__(self):
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
        gray_frame = cv2.cvtColor(working_frame, cv2.COLOR_BGR2GRAY)
        detect_frame = cv2.equalizeHist(gray_frame)
        faces = self._detect_faces(detect_frame)

        if faces:
            return self._score_with_faces(gray_frame, faces)

        return self._score_without_faces(gray_frame)

    def _downscale(self, frame):
        if FACE_DETECT_SCALE <= 0 or FACE_DETECT_SCALE >= 1:
            return frame

        height, width = frame.shape[:2]
        resized_width = max(1, int(width * FACE_DETECT_SCALE))
        resized_height = max(1, int(height * FACE_DETECT_SCALE))
        return cv2.resize(
            frame,
            (resized_width, resized_height),
            interpolation=cv2.INTER_AREA
        )

    def _detect_faces(self, gray_frame):
        if self.face_cascade is None:
            return []

        min_dimension = min(gray_frame.shape[:2])
        min_face_size = max(24, int(min_dimension * 0.14))

        try:
            faces = self.face_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.15,
                minNeighbors=4,
                minSize=(min_face_size, min_face_size)
            )
        except Exception:
            return []

        return list(faces) if len(faces) else []

    def _score_with_faces(self, gray_frame, faces):
        frame_height, frame_width = gray_frame.shape[:2]
        frame_area = float(frame_height * frame_width) or 1.0

        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x_pos, y_pos, width, height = largest_face
        face_area = float(width * height)
        face_ratio = face_area / frame_area

        face_crop = gray_frame[y_pos:y_pos + height, x_pos:x_pos + width]
        blur_variance = self._laplacian_variance(face_crop)
        brightness_value = float(face_crop.mean()) if face_crop.size else 0.0

        centered_score = self._centered_score(
            frame_width,
            frame_height,
            x_pos,
            y_pos,
            width,
            height
        )
        size_score = self._size_score(face_ratio)
        edge_score = self._edge_score(
            frame_width,
            frame_height,
            x_pos,
            y_pos,
            width,
            height
        )
        sharpness_score = self._sharpness_score_from_variance(blur_variance)
        brightness_score = self._brightness_score_from_value(brightness_value)
        dominant_score = self._dominant_face_score(faces)

        total_score = _clamp(
            0.30 * centered_score +
            0.24 * size_score +
            0.14 * edge_score +
            0.16 * sharpness_score +
            0.10 * brightness_score +
            0.06 * dominant_score
        )

        if len(faces) == 1:
            total_score = _clamp(total_score + 0.08)
        else:
            total_score = _clamp(total_score - 0.18 * min(len(faces) - 1, 2))

        total_score = _clamp(
            total_score
            - 0.18 * (1.0 - size_score)
            - 0.16 * (1.0 - centered_score)
            - 0.14 * (1.0 - edge_score)
            - 0.12 * (1.0 - sharpness_score)
            - 0.08 * (1.0 - brightness_score)
        )

        single_clear_face = (
            len(faces) == 1 and
            face_ratio >= MIN_FACE_SIZE_RATIO and
            centered_score >= CLEAR_FACE_CENTER_SCORE and
            edge_score >= CLEAR_FACE_EDGE_SCORE and
            blur_variance >= BLUR_THRESHOLD and
            BRIGHTNESS_MIN <= brightness_value <= BRIGHTNESS_MAX
        )

        return FrameMetrics(
            total_score=total_score,
            acceptable=single_clear_face,
            used_face_detection=True,
            face_count=len(faces),
            centered_score=centered_score,
            size_score=size_score,
            edge_score=edge_score,
            sharpness_score=sharpness_score,
            brightness_score=brightness_score,
            heuristic_score=dominant_score,
            face_ratio=face_ratio,
            single_clear_face=single_clear_face,
            blur_variance=blur_variance,
            brightness_value=brightness_value
        )

    def _score_without_faces(self, gray_frame):
        blur_variance = self._laplacian_variance(gray_frame)
        brightness_value = float(gray_frame.mean()) if gray_frame.size else 0.0

        sharpness_score = self._sharpness_score_from_variance(blur_variance)
        brightness_score = self._brightness_score_from_value(brightness_value)
        centered_score = self._general_centered_score(gray_frame)
        contrast_score = self._contrast_score(gray_frame)

        total_score = _clamp(
            0.40 * sharpness_score +
            0.24 * brightness_score +
            0.22 * centered_score +
            0.14 * contrast_score
        )

        acceptable = (
            blur_variance >= BLUR_THRESHOLD and
            BRIGHTNESS_MIN <= brightness_value <= BRIGHTNESS_MAX
        )

        return FrameMetrics(
            total_score=total_score,
            acceptable=acceptable,
            used_face_detection=False,
            face_count=0,
            centered_score=centered_score,
            size_score=0.0,
            edge_score=0.0,
            sharpness_score=sharpness_score,
            brightness_score=brightness_score,
            heuristic_score=contrast_score,
            face_ratio=0.0,
            single_clear_face=False,
            blur_variance=blur_variance,
            brightness_value=brightness_value
        )

    def _centered_score(self, frame_width, frame_height, x_pos, y_pos, width, height):
        face_center_x = x_pos + (width / 2.0)
        face_center_y = y_pos + (height / 2.0)
        frame_center_x = frame_width / 2.0
        frame_center_y = frame_height / 2.0

        tolerance_x = max(1.0, frame_width * CENTER_TOLERANCE_RATIO)
        tolerance_y = max(1.0, frame_height * CENTER_TOLERANCE_RATIO)

        delta_x = abs(face_center_x - frame_center_x) / tolerance_x
        delta_y = abs(face_center_y - frame_center_y) / tolerance_y
        return _clamp(1.0 - (math.hypot(delta_x, delta_y) / 2.0))

    def _size_score(self, face_ratio):
        if face_ratio <= 0:
            return 0.0

        if face_ratio < MIN_FACE_SIZE_RATIO:
            return _clamp(0.6 * (face_ratio / MIN_FACE_SIZE_RATIO))

        ideal_ratio = min(0.20, max(MIN_FACE_SIZE_RATIO * 2.5, 0.08))
        if face_ratio <= ideal_ratio:
            range_size = max(ideal_ratio - MIN_FACE_SIZE_RATIO, 0.01)
            return _clamp(
                0.6 + (0.4 * ((face_ratio - MIN_FACE_SIZE_RATIO) / range_size))
            )

        return _clamp(1.0 - ((face_ratio - ideal_ratio) / max(ideal_ratio * 0.85, 0.01)))

    def _edge_score(self, frame_width, frame_height, x_pos, y_pos, width, height):
        min_margin = min(
            x_pos,
            y_pos,
            max(0, frame_width - (x_pos + width)),
            max(0, frame_height - (y_pos + height))
        )
        target_margin = min(frame_width, frame_height) * 0.07
        if target_margin <= 0:
            return 0.0
        return _clamp(min_margin / target_margin)

    def _dominant_face_score(self, faces):
        if len(faces) == 1:
            return 1.0

        areas = sorted((face[2] * face[3] for face in faces), reverse=True)
        total_area = float(sum(areas)) or 1.0
        return _clamp(areas[0] / total_area)

    def _laplacian_variance(self, gray_frame):
        if gray_frame.size == 0:
            return 0.0
        return float(cv2.Laplacian(gray_frame, cv2.CV_64F).var())

    def _sharpness_score_from_variance(self, variance):
        return _clamp(variance / max(BLUR_THRESHOLD * 3.0, 1.0))

    def _brightness_score_from_value(self, brightness_value):
        if BRIGHTNESS_MIN <= brightness_value <= BRIGHTNESS_MAX:
            return 1.0

        if brightness_value < BRIGHTNESS_MIN:
            return _clamp(brightness_value / max(BRIGHTNESS_MIN, 1.0))

        return _clamp(
            (255.0 - brightness_value) / max(255.0 - BRIGHTNESS_MAX, 1.0)
        )

    def _contrast_score(self, gray_frame):
        if gray_frame.size == 0:
            return 0.0

        contrast = float(gray_frame.std())
        return _clamp(contrast / 64.0)

    def _general_centered_score(self, gray_frame):
        if gray_frame.size == 0:
            return 0.0

        energy_frame = cv2.convertScaleAbs(cv2.Laplacian(gray_frame, cv2.CV_32F))
        total_energy = float(energy_frame.sum())
        if total_energy <= 0:
            return 0.5

        frame_height, frame_width = energy_frame.shape[:2]
        half_box_width = max(1, int(frame_width * CENTER_TOLERANCE_RATIO))
        half_box_height = max(1, int(frame_height * CENTER_TOLERANCE_RATIO))
        center_x = frame_width // 2
        center_y = frame_height // 2

        x1 = max(0, center_x - half_box_width)
        y1 = max(0, center_y - half_box_height)
        x2 = min(frame_width, center_x + half_box_width)
        y2 = min(frame_height, center_y + half_box_height)

        center_energy = float(energy_frame[y1:y2, x1:x2].sum())
        center_area_ratio = float((x2 - x1) * (y2 - y1)) / float(frame_width * frame_height)
        if center_area_ratio <= 0:
            return 0.5

        return _clamp(
            (center_energy / total_energy) / max(center_area_ratio * 1.2, 0.01)
        )


class CaptureService:
    BUFFER_SLEEP_SEC = max(0.05, FRAME_SAMPLE_INTERVAL_MS / 1000.0)

    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
        self.scorer = BestFrameScorer()
        self.buffer = deque(maxlen=MAX_BUFFER_FRAMES)
        self.buffer_lock = threading.Lock()
        self.buffer_thread = None
        self.buffer_stop_event = threading.Event()
        self.enrollment_capture = None
        self.enrollment_lock = threading.Lock()

    def start_camera(self):
        if not self.camera_manager.start_camera():
            return False

        self._start_buffer_worker()
        return True

    def stop_camera(self):
        self.cancel_enrollment_session()
        self._stop_buffer_worker()
        self.camera_manager.release()

    def is_camera_running(self):
        return self.camera_manager.running

    def trigger_capture_event(self):
        if not self.start_camera():
            return None

        return EventCapture(self, time.monotonic())

    def capture_known_user(self, person_name, identity_value=None, event_capture=None):
        existing_photo_path = self.camera_manager.find_saved_photo_for_today(
            person_name,
            identity_value
        )
        if existing_photo_path:
            if event_capture:
                event_capture.cancel()
            print("[Capture] Reusing today's existing photo:", existing_photo_path)
            return True, existing_photo_path, None

        capture = event_capture or self.trigger_capture_event()
        if capture is None:
            return False, None, None

        result = self._resolve_event_capture(capture)
        if result.frame is not None:
            success, path = self.camera_manager.save_frame(
                person_name,
                result.frame,
                identity_value=identity_value
            )
            if success:
                return True, path, result.metrics

        success, path = self.camera_manager.capture_image(
            person_name,
            identity_value=identity_value
        )
        return success, path, result.metrics

    def start_enrollment_session(self, event_capture=None):
        capture = event_capture or self.trigger_capture_event()
        if capture is None:
            return False

        with self.enrollment_lock:
            self._clear_enrollment_capture_locked()
            self.enrollment_capture = capture
            return True

    def finalize_enrollment_capture(self, person_name, identity_value=None):
        existing_photo_path = self.camera_manager.find_saved_photo_for_today(
            person_name,
            identity_value
        )
        if existing_photo_path:
            with self.enrollment_lock:
                capture = self.enrollment_capture
                self.enrollment_capture = None
            if capture:
                capture.cancel()
            print("[Capture] Reusing today's existing photo:", existing_photo_path)
            return True, existing_photo_path, None

        with self.enrollment_lock:
            capture = self.enrollment_capture
            self.enrollment_capture = None

        result = self._resolve_event_capture(capture)
        if result.frame is not None:
            success, path = self.camera_manager.save_frame(
                person_name,
                result.frame,
                identity_value=identity_value
            )
            if success:
                return True, path, result.metrics

        success, path = self.camera_manager.capture_image(
            person_name,
            identity_value=identity_value
        )
        return success, path, result.metrics

    def cancel_enrollment_session(self):
        with self.enrollment_lock:
            self._clear_enrollment_capture_locked()

    def select_event_result(self, event_time):
        candidates = self._snapshot_candidates(event_time)
        best_candidate = self._select_best_candidate(candidates, event_time)

        if best_candidate is None:
            return CaptureResult(
                frame=None,
                metrics=None,
                used_event_candidate=False
            )

        if DEBUG_SAVE_FRAMES:
            self._save_debug_frame(best_candidate, event_time)

        return CaptureResult(
            frame=best_candidate.frame.copy(),
            metrics=best_candidate.metrics,
            used_event_candidate=True
        )

    def _start_buffer_worker(self):
        if self.buffer_thread and self.buffer_thread.is_alive():
            return

        self.buffer_stop_event.clear()
        self.buffer_thread = threading.Thread(target=self._buffer_loop, daemon=True)
        self.buffer_thread.start()

    def _stop_buffer_worker(self):
        self.buffer_stop_event.set()
        if self.buffer_thread:
            self.buffer_thread.join(timeout=1)

        self.buffer_thread = None
        with self.buffer_lock:
            self.buffer.clear()

    def _buffer_loop(self):
        while not self.buffer_stop_event.is_set():
            frame = self.camera_manager.get_frame()
            if frame is not None:
                metrics = self.scorer.evaluate(frame)
                if metrics is not None:
                    self._append_buffered_frame(frame, metrics)

            self.buffer_stop_event.wait(self.BUFFER_SLEEP_SEC)

    def _append_buffered_frame(self, frame, metrics):
        timestamp = time.monotonic()
        with self.buffer_lock:
            self.buffer.append(
                BufferedFrame(
                    timestamp=timestamp,
                    frame=frame,
                    metrics=metrics
                )
            )
            self._trim_buffer_locked(timestamp)

    def _trim_buffer_locked(self, now):
        cutoff = now - BUFFER_DURATION_SEC
        while self.buffer and self.buffer[0].timestamp < cutoff:
            self.buffer.popleft()

    def _snapshot_candidates(self, event_time):
        window_start = event_time - PRE_EVENT_WINDOW_SEC
        window_end = event_time + POST_EVENT_WINDOW_SEC

        with self.buffer_lock:
            self._trim_buffer_locked(time.monotonic())
            return [
                candidate
                for candidate in self.buffer
                if window_start <= candidate.timestamp <= window_end
            ]

    def _select_best_candidate(self, candidates, event_time):
        if not candidates:
            return None

        clear_single_face = [
            candidate
            for candidate in candidates
            if candidate.metrics.single_clear_face
        ]
        if clear_single_face:
            return max(
                clear_single_face,
                key=lambda candidate: self._single_face_candidate_score(candidate, event_time)
            )

        face_candidates = [
            candidate
            for candidate in candidates
            if candidate.metrics.face_count > 0
        ]
        if face_candidates:
            return max(
                face_candidates,
                key=lambda candidate: self._face_candidate_score(candidate, event_time)
            )

        return max(
            candidates,
            key=lambda candidate: self._general_candidate_score(candidate, event_time)
        )

    def _single_face_candidate_score(self, candidate, event_time):
        metrics = candidate.metrics
        timing_score = self._timing_score(candidate.timestamp, event_time)
        return (
            metrics.total_score +
            0.14 * metrics.size_score +
            0.12 * metrics.centered_score +
            0.10 * metrics.edge_score +
            0.10 * timing_score
        )

    def _face_candidate_score(self, candidate, event_time):
        metrics = candidate.metrics
        timing_score = self._timing_score(candidate.timestamp, event_time)
        multi_face_penalty = 0.22 * min(max(metrics.face_count - 1, 0), 2)
        return (
            metrics.total_score +
            0.18 * timing_score +
            0.12 * (1.0 if metrics.face_count == 1 else 0.0) -
            multi_face_penalty -
            0.24 * (1.0 - metrics.size_score) -
            0.22 * (1.0 - metrics.centered_score) -
            0.20 * (1.0 - metrics.edge_score) -
            0.16 * (1.0 - metrics.sharpness_score) -
            0.12 * (1.0 - metrics.brightness_score)
        )

    def _general_candidate_score(self, candidate, event_time):
        metrics = candidate.metrics
        timing_score = self._timing_score(candidate.timestamp, event_time)
        return (
            metrics.total_score +
            0.18 * timing_score -
            0.14 * (1.0 - metrics.sharpness_score) -
            0.12 * (1.0 - metrics.brightness_score) -
            0.10 * (1.0 - metrics.centered_score)
        )

    def _timing_score(self, timestamp, event_time):
        delta = timestamp - event_time
        preferred_post = min(max(PREFERRED_POST_EVENT_SEC, 0.0), POST_EVENT_WINDOW_SEC)

        if delta < 0:
            progress = 1.0 - (abs(delta) / max(PRE_EVENT_WINDOW_SEC, 0.01))
            return _clamp(0.20 + (0.25 * progress))

        if preferred_post <= 0:
            return 1.0

        if delta <= preferred_post:
            return _clamp(0.55 + (0.45 * (delta / preferred_post)))

        remaining_window = max(POST_EVENT_WINDOW_SEC - preferred_post, 0.01)
        return _clamp(1.0 - (0.45 * ((delta - preferred_post) / remaining_window)))

    def _resolve_event_capture(self, capture):
        if capture is None:
            return CaptureResult(
                frame=None,
                metrics=None,
                used_event_candidate=False
            )

        result = capture.wait()
        if result is not None:
            return result

        return CaptureResult(
            frame=None,
            metrics=None,
            used_event_candidate=False
        )

    def _clear_enrollment_capture_locked(self):
        if self.enrollment_capture:
            self.enrollment_capture.cancel()
            self.enrollment_capture = None

    def _save_debug_frame(self, candidate, event_time):
        debug_folder = os.path.join(DATA_PHOTOS_FOLDER, "debug")
        os.makedirs(debug_folder, exist_ok=True)

        metrics = candidate.metrics
        label = "general"
        if metrics.single_clear_face:
            label = "single_face"
        elif metrics.face_count > 0:
            label = "face"

        filename = "event_{0}_{1}_{2:.3f}.jpg".format(
            int(event_time * 1000),
            label,
            metrics.total_score
        )
        cv2.imwrite(os.path.join(debug_folder, filename), candidate.frame)
