from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl


class VideoPlayer(QVideoWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # 使用 QMediaPlaylist 实现无限循环播放
        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)

        self.player.setPlaylist(self.playlist)
        self.player.setVideoOutput(self)
        self.player.setVolume(0)  # 背景视频默认无声

    def load_and_play(self, filepath):
        if filepath:
            self.playlist.clear()
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
            self.player.play()

    def stop(self):
        self.player.stop()