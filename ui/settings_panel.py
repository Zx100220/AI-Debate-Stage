import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QFileDialog, QScrollArea, QFrame)
from PyQt5.QtCore import Qt


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 240); color: white; border-radius: 10px;")

        self.config_file = "config.json"

        # 构建UI
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)

        # 关闭按钮（顶部右对齐）
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self.btn_close = QPushButton("✕")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setStyleSheet(
            "QPushButton { background-color: #555; color: white; border-radius: 16px; font-size: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #D83B01; }"
        )
        close_layout.addWidget(self.btn_close)
        self.layout.addLayout(close_layout)

        # 1. 基础配置
        self.layout.addWidget(QLabel("<h2>🔨 通用配置</h2>"))
        self.topic_input = self._add_row("当期辩题：")
        self.rounds_input = self._add_row("辩论轮数：", "3")

        # 视频路径
        video_layout = QHBoxLayout()
        self.video_input = QLineEdit()
        btn_browse = QPushButton("选择视频")
        btn_browse.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        btn_browse.clicked.connect(self._browse_video)
        video_layout.addWidget(self.video_input)
        video_layout.addWidget(btn_browse)
        self.layout.addWidget(QLabel("背景视频路径："))
        self.layout.addLayout(video_layout)

        # 2. AI 1 设置
        self.layout.addWidget(QLabel("<h2>🤖 AI 1 (左侧/正方) 配置</h2>"))
        self.ai1_name = self._add_row("名称：", "正方")
        self.ai1_viewpoint = self._add_row("正方观点：")
        self.ai1_url = self._add_row("API URL：")
        self.ai1_model = self._add_row("模型名称：")
        self.ai1_key = self._add_row("API 密钥：", is_password=True)
        self.ai1_style = self._add_row("发言风格 (Prompt)：")

        # 3. AI 2 设置
        self.layout.addWidget(QLabel("<h2>🤖 AI 2 (右侧/反方) 配置</h2>"))
        self.ai2_name = self._add_row("名称：", "反方")
        self.ai2_viewpoint = self._add_row("反方观点：")
        self.ai2_url = self._add_row("API URL：")
        self.ai2_model = self._add_row("模型名称：")
        self.ai2_key = self._add_row("API 密钥：", is_password=True)
        self.ai2_style = self._add_row("发言风格 (Prompt)：")

        self.layout.addStretch()

        # 回写到ScrollArea
        scroll.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        # 控制按钮组
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 保存配置")
        self.btn_start = QPushButton("▶️ 开始辩论")
        self.btn_stop = QPushButton("⏹ 停止辩论")

        for btn in [self.btn_save, self.btn_start, self.btn_stop]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #555; border-radius: 5px;")
            btn_layout.addWidget(btn)

        self.btn_start.setStyleSheet(self.btn_start.styleSheet() + "background-color: #0078D7;")
        self.btn_stop.setStyleSheet(self.btn_stop.styleSheet() + "background-color: #D83B01;")

        main_layout.addLayout(btn_layout)

    def _add_row(self, label_text, default="", is_password=False):
        self.layout.addWidget(QLabel(label_text))
        line_edit = QLineEdit(default)
        line_edit.setStyleSheet("background-color: #444; border: 1px solid #666; padding: 5px; border-radius: 3px;")
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(line_edit)
        return line_edit

    def _browse_video(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "选择背景视频", "", "视频文件 (*.mp4 *.avi *.mkv)")
        if filepath:
            self.video_input.setText(filepath)

    def get_config(self):
        return {
            "topic": self.topic_input.text(),
            "rounds": self.rounds_input.text(),
            "video_path": self.video_input.text(),
            "ai1": {
                "name": self.ai1_name.text(),
                "viewpoint": self.ai1_viewpoint.text(),
                "api_url": self.ai1_url.text(),
                "model_name": self.ai1_model.text(),
                "api_key": self.ai1_key.text(),
                "style": self.ai1_style.text()
            },
            "ai2": {
                "name": self.ai2_name.text(),
                "viewpoint": self.ai2_viewpoint.text(),
                "api_url": self.ai2_url.text(),
                "model_name": self.ai2_model.text(),
                "api_key": self.ai2_key.text(),
                "style": self.ai2_style.text()
            }
        }

    def load_config(self, config_data):
        self.topic_input.setText(config_data.get("topic", ""))
        self.rounds_input.setText(str(config_data.get("rounds", "3")))
        self.video_input.setText(config_data.get("video_path", ""))

        ai1 = config_data.get("ai1", {})
        self.ai1_name.setText(ai1.get("name", ""))
        self.ai1_viewpoint.setText(ai1.get("viewpoint", ""))
        self.ai1_url.setText(ai1.get("api_url", ""))
        self.ai1_model.setText(ai1.get("model_name", ""))
        self.ai1_key.setText(ai1.get("api_key", ""))
        self.ai1_style.setText(ai1.get("style", ""))

        ai2 = config_data.get("ai2", {})
        self.ai2_name.setText(ai2.get("name", ""))
        self.ai2_viewpoint.setText(ai2.get("viewpoint", ""))
        self.ai2_url.setText(ai2.get("api_url", ""))
        self.ai2_model.setText(ai2.get("model_name", ""))
        self.ai2_key.setText(ai2.get("api_key", ""))
        self.ai2_style.setText(ai2.get("style", ""))