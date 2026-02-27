import os

import cv2
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap


class VideoPlayer(QLabel):
    """使用 OpenCV 读取视频帧并通过 QLabel 显示，替代不可靠的 Qt 多媒体后端。"""

    DEFAULT_FPS = 30
    error_sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")

        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._current_path = ""

    def _next_frame(self):
        if self._cap is None or not self._cap.isOpened():
            return

        ret, frame = self._cap.read()
        if not ret:
            # 视频结束，循环播放
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
            if not ret:
                return

        # BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape

        # 缩放到当前控件尺寸，保持宽高比
        label_w, label_h = self.width(), self.height()
        if label_w > 0 and label_h > 0:
            scale = min(label_w / w, label_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w, ch = frame.shape

        qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.setPixmap(QPixmap.fromImage(qimg))

    def load_and_play(self, filepath):
        abs_path = os.path.abspath(filepath) if filepath else ""
        if abs_path and os.path.isfile(abs_path):
            if abs_path == self._current_path and self._timer.isActive():
                return
            self.stop()
            self._current_path = abs_path

            cap = cv2.VideoCapture(abs_path)
            if not cap.isOpened():
                self.error_sig.emit(f"无法打开视频文件: {abs_path}")
                return

            self._cap = cap
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = self.DEFAULT_FPS
            self._timer.start(int(1000 / fps))
        elif filepath:
            self.error_sig.emit(f"视频文件不存在: {filepath}")

    def stop(self):
        self._timer.stop()
        self._current_path = ""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self.clear()