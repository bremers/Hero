"""Face and presence detection using MediaPipe."""

import subprocess
import threading
from pathlib import Path

import cv2
import mediapipe as mp
from loguru import logger

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
MODEL_PATH = Path("models/blaze_face_short_range.tflite")

# Keypoint indices from FaceDetector
RIGHT_EYE, LEFT_EYE, NOSE_TIP = 0, 1, 2


def _ensure_model() -> Path:
    if MODEL_PATH.exists():
        return MODEL_PATH
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading face detection model...")
    subprocess.run(
        ["curl", "-sL", "-o", str(MODEL_PATH), MODEL_URL],
        check=True,
    )
    logger.info(f"Saved to {MODEL_PATH}")
    return MODEL_PATH


def _is_facing_camera(keypoints: list, symmetry_threshold: float) -> bool:
    """Check if a face is roughly facing the camera using keypoint symmetry."""
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
        model_path = _ensure_model()

        base_options = mp.tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp.tasks.vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            min_detection_confidence=detection_confidence,
        )
        self._detector = mp.tasks.vision.FaceDetector.create_from_options(options)
        self._symmetry_threshold = symmetry_threshold
        self._poll_interval = poll_interval

        self._cap = cv2.VideoCapture(camera_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {camera_index}")
        logger.info(f"Camera {camera_index} opened")

        self._addressed = False
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
            result = self._detector.detect(mp_image)

            addressed = any(
                _is_facing_camera(d.keypoints, self._symmetry_threshold) for d in result.detections
            )

            with self._lock:
                self._addressed = addressed

            if addressed and not was_addressed:
                logger.info("Addressee detected — face facing camera")
            elif not addressed and was_addressed:
                logger.info("Addressee lost — no face facing camera")
            was_addressed = addressed

            self._stop.wait(self._poll_interval)

    @property
    def is_addressed(self) -> bool:
        with self._lock:
            return self._addressed

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._cap.release()
        self._detector.close()
        logger.info("Presence detector closed")

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self.close()
