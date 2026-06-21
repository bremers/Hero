"""Face and presence detection + wave gesture using MediaPipe."""

import subprocess
import threading
from pathlib import Path

import cv2
import mediapipe as mp
from loguru import logger

FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
FACE_MODEL_PATH = Path("models/blaze_face_short_range.tflite")

GESTURE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task"
GESTURE_MODEL_PATH = Path("models/gesture_recognizer.task")

RIGHT_EYE, LEFT_EYE, NOSE_TIP = 0, 1, 2

# Number of consecutive open-palm frames to count as a wave (~1s at 10fps)
WAVE_FRAMES_REQUIRED = 8


def _ensure_model(path: Path, url: str) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {path.name}...")
    subprocess.run(["curl", "-sL", "-o", str(path), url], check=True)
    logger.info(f"Saved to {path}")
    return path


def _is_facing_camera(keypoints: list, symmetry_threshold: float) -> bool:
    if not keypoints or len(keypoints) < 3:
        return False
    nose = keypoints[NOSE_TIP]
    left_eye = keypoints[LEFT_EYE]
    right_eye = keypoints[RIGHT_EYE]

    dist_left = abs(nose.x - left_eye.x)
    dist_right = abs(nose.x - right_eye.x)

    if max(dist_left, dist_right) < 1e-6:
        return False

    ratio = min(dist_left, dist_right) / max(dist_left, dist_right)
    return ratio >= symmetry_threshold


class PresenceDetector:
    def __init__(
        self,
        camera_index: int = 0,
        detection_confidence: float = 0.5,
        symmetry_threshold: float = 0.6,
        poll_interval: float = 0.1,
    ) -> None:
        face_path = _ensure_model(FACE_MODEL_PATH, FACE_MODEL_URL)
        gesture_path = _ensure_model(GESTURE_MODEL_PATH, GESTURE_MODEL_URL)

        face_opts = mp.tasks.vision.FaceDetectorOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(face_path)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            min_detection_confidence=detection_confidence,
        )
        self._face_detector = mp.tasks.vision.FaceDetector.create_from_options(face_opts)

        gesture_opts = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(gesture_path)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.3,
            min_tracking_confidence=0.3,
        )
        self._gesture_recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(
            gesture_opts
        )

        self._symmetry_threshold = symmetry_threshold
        self._poll_interval = poll_interval

        self._cap = cv2.VideoCapture(camera_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {camera_index}")
        logger.info(f"Camera {camera_index} opened")

        self._addressed = False
        self._wave_detected = False
        self._palm_streak = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        was_addressed = False
        while not self._stop.is_set():
            ret, frame = self._cap.read()
            if not ret:
                self._stop.wait(self._poll_interval)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # Face detection
            face_result = self._face_detector.detect(mp_image)
            addressed = any(
                _is_facing_camera(d.keypoints, self._symmetry_threshold)
                for d in face_result.detections
            )

            # Gesture detection — sustained open palm = wave
            wave = False
            gesture_result = self._gesture_recognizer.recognize(mp_image)
            if gesture_result.gestures:
                gesture_name = gesture_result.gestures[0][0].category_name
                confidence = gesture_result.gestures[0][0].score
                if gesture_name == "Open_Palm" and confidence > 0.5:
                    self._palm_streak += 1
                    if self._palm_streak == WAVE_FRAMES_REQUIRED:
                        wave = True
                else:
                    self._palm_streak = 0
            else:
                self._palm_streak = 0

            with self._lock:
                self._addressed = addressed
                if wave:
                    self._wave_detected = True

            if addressed and not was_addressed:
                logger.info("Addressee detected — face facing camera")
            elif not addressed and was_addressed:
                logger.info("Addressee lost — no face facing camera")
            if wave:
                logger.info("Wave gesture detected (sustained open palm)")
            was_addressed = addressed

            self._stop.wait(self._poll_interval)

    @property
    def is_addressed(self) -> bool:
        with self._lock:
            return self._addressed

    @property
    def detected_wave(self) -> bool:
        with self._lock:
            if self._wave_detected:
                self._wave_detected = False
                return True
            return False

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._cap.release()
        self._face_detector.close()
        self._gesture_recognizer.close()
        logger.info("Presence detector closed")

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self.close()
