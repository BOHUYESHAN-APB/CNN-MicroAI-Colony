import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass
class FramePacket:
    seq: int
    timestamp: float
    frame_bgr: np.ndarray


class CameraService:
    def __init__(
        self, camera_index: int = 0, width: int = 1280, height: int = 720, fps: int = 30
    ):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._latest: Optional[FramePacket] = None
        self._seq = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        if self._running:
            return True
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)

        self._cap = cap
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="camera-loop", daemon=True
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _loop(self) -> None:
        assert self._cap is not None
        frame_interval = 1.0 / max(self.fps, 1)
        while self._running:
            t0 = time.time()
            ok, frame = self._cap.read()
            if ok and frame is not None:
                self._seq += 1
                pkt = FramePacket(seq=self._seq, timestamp=t0, frame_bgr=frame)
                with self._lock:
                    self._latest = pkt
            dt = time.time() - t0
            if dt < frame_interval:
                time.sleep(frame_interval - dt)

    def get_latest(self) -> Optional[FramePacket]:
        with self._lock:
            if self._latest is None:
                return None
            return FramePacket(
                seq=self._latest.seq,
                timestamp=self._latest.timestamp,
                frame_bgr=self._latest.frame_bgr.copy(),
            )
