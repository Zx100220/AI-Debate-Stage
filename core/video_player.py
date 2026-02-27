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

        self.player.error.connect(self._on_player_error)

    def _on_player_error(self, error):
        error_msg = self.player.errorString()
        self.player.stop()
        self.playlist.clear()
        self.error_sig.emit(f"视频播放失败: {error_msg}")

    def load_and_play(self, filepath):
        if filepath and os.path.isfile(filepath):
            self.playlist.clear()
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
            self.player.play()
        elif filepath:
            self.error_sig.emit(f"视频文件不存在: {filepath}")

    def stop(self):
        self.player.stop()