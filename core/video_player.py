import os

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, pyqtSignal


class VideoPlayer(QVideoWidget):
    error_sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # 使用 QMediaPlaylist 实现无限循环播放
        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)

        self.player.setPlaylist(self.playlist)
        self.player.setVideoOutput(self)
        self.player.setVolume(0)  # 背景视频默认无声

        self._pending_play = False
        self._current_path = ""

        self.player.error.connect(self._on_player_error)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia and self._pending_play:
            self._pending_play = False
            self.player.play()
        elif status == QMediaPlayer.InvalidMedia:
            self._pending_play = False
            self._current_path = ""
            self.player.stop()
            self.playlist.clear()
            self.error_sig.emit("视频格式不支持或文件损坏，已跳过视频播放")

    def _on_player_error(self, error):
        self._pending_play = False
        self._current_path = ""
        error_msg = self.player.errorString()
        self.player.stop()
        self.playlist.clear()
        self.error_sig.emit(f"视频播放失败: {error_msg}")

    def load_and_play(self, filepath):
        abs_path = os.path.abspath(filepath) if filepath else ""
        if abs_path and os.path.isfile(abs_path):
            if abs_path == self._current_path and self.player.state() != QMediaPlayer.StoppedState:
                return
            self.player.stop()
            self.playlist.clear()
            self._current_path = abs_path
            self._pending_play = True
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(abs_path)))
        elif filepath:
            self.error_sig.emit(f"视频文件不存在: {filepath}")

    def stop(self):
        self._pending_play = False
        self._current_path = ""
        self.player.stop()