import json
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                             QFileDialog, QVBoxLayout, QShortcut)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPixmap, QKeySequence, QIcon

from core.video_player import VideoPlayer
from core.debate_engine import DebateEngine
from ui.settings_panel import SettingsPanel
from ui.history_panel import HistoryPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(540, 960)
        self.setWindowTitle("AI 辩论台")
        self.setStyleSheet("background-color: black;")

        self.engine = None
        self.config_file = "config.json"

        # 外部弹出面板状态
        self._settings_visible = False
        self._history_visible = False

        # 字幕相关状态
        self._subtitle_buffer = ""       # 当前流式积累的文本
        self._current_speaker = ""       # 当前说话者名称
        self._current_color = "#FFFFFF"  # 当前说话者颜色

        # 对话记录缓存（用于历史面板）
        self._history_messages = []
        self._current_message_text = ""

        # 头像图片路径
        self._ai1_avatar_path = ""
        self._ai2_avatar_path = ""

        self._init_ui()
        self._init_shortcuts()
        self._load_config()

    def _init_ui(self):
        # 0. 底层视频播放器
        self.video_player = VideoPlayer(self)
        self.video_player.error_sig.connect(
            lambda msg: self._show_subtitle(f"[警告] {msg}")
        )

        # ----------- 绝对定位的浮层 -----------
        # 1. 顶部区域：辩题和头像
        self.top_layer = QWidget(self)
        self.top_layer.setStyleSheet("background-color: rgba(0, 0, 0, 0);")

        # 辩题标签 - 美化
        self.lbl_topic = QLabel("未设置辩题", self.top_layer)
        self.lbl_topic.setAlignment(Qt.AlignCenter)
        self.lbl_topic.setWordWrap(True)
        self.lbl_topic.setStyleSheet("""
            QLabel {
                color: #FFD700;
                font-weight: bold;
                font-size: 22px;
                padding: 12px 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 30, 60, 220),
                    stop:0.5 rgba(50, 20, 80, 220),
                    stop:1 rgba(30, 30, 60, 220));
                border: 2px solid rgba(255, 215, 0, 100);
                border-radius: 12px;
            }
        """)

        # 正方头像区域（左侧）
        self.ai1_widget = QWidget(self.top_layer)
        self.ai1_layout = QVBoxLayout(self.ai1_widget)
        self.ai1_layout.setContentsMargins(0, 0, 0, 0)
        self.ai1_layout.setSpacing(4)

        self.lbl_ai1_avatar = QPushButton(self.ai1_widget)
        self.lbl_ai1_avatar.setCursor(Qt.PointingHandCursor)
        self.lbl_ai1_avatar.setText("正")
        self.lbl_ai1_avatar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 35px;
                font-weight: bold;
                font-size: 22px;
                border: 3px solid rgba(255, 255, 255, 150);
            }
            QPushButton:hover { border: 3px solid #FFD700; }
        """)
        self.lbl_ai1_avatar.clicked.connect(lambda: self._pick_avatar("ai1"))
        self.ai1_layout.addWidget(self.lbl_ai1_avatar, alignment=Qt.AlignCenter)

        self.lbl_ai1_name = QLabel("正方", self.ai1_widget)
        self.lbl_ai1_name.setAlignment(Qt.AlignCenter)
        self.lbl_ai1_name.setStyleSheet(
            "color: #80D8FF; font-size: 13px; font-weight: bold; background: transparent;"
        )
        self.ai1_layout.addWidget(self.lbl_ai1_name)

        # 反方头像区域（右侧）
        self.ai2_widget = QWidget(self.top_layer)
        self.ai2_layout = QVBoxLayout(self.ai2_widget)
        self.ai2_layout.setContentsMargins(0, 0, 0, 0)
        self.ai2_layout.setSpacing(4)

        self.lbl_ai2_avatar = QPushButton(self.ai2_widget)
        self.lbl_ai2_avatar.setCursor(Qt.PointingHandCursor)
        self.lbl_ai2_avatar.setText("反")
        self.lbl_ai2_avatar.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 35px;
                font-weight: bold;
                font-size: 22px;
                border: 3px solid rgba(255, 255, 255, 150);
            }
            QPushButton:hover { border: 3px solid #FFD700; }
        """)
        self.lbl_ai2_avatar.clicked.connect(lambda: self._pick_avatar("ai2"))
        self.ai2_layout.addWidget(self.lbl_ai2_avatar, alignment=Qt.AlignCenter)

        self.lbl_ai2_name = QLabel("反方", self.ai2_widget)
        self.lbl_ai2_name.setAlignment(Qt.AlignCenter)
        self.lbl_ai2_name.setStyleSheet(
            "color: #FF8A80; font-size: 13px; font-weight: bold; background: transparent;"
        )
        self.ai2_layout.addWidget(self.lbl_ai2_name)

        # 2. 底部字幕区域 - 使用 QLabel 实现句号切换
        self.bottom_layer = QLabel(self)
        self.bottom_layer.setAlignment(Qt.AlignCenter)
        self.bottom_layer.setWordWrap(True)
        self.bottom_layer.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: #FFFFFF;
                font-size: 22px;
                border: none;
                padding: 15px 20px;
                border-radius: 10px;
            }
        """)

        # 3. 设置面板（外部弹出，右侧）
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.settings_panel.btn_save.clicked.connect(self._save_config)
        self.settings_panel.btn_start.clicked.connect(self.start_debate)
        self.settings_panel.btn_stop.clicked.connect(self.stop_debate)
        self.settings_panel.hide()

        # 4. 对话记录面板（外部弹出，左侧）
        self.history_panel = HistoryPanel(self)
        self.history_panel.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.history_panel.hide()

    def _init_shortcuts(self):
        """注册键盘快捷键"""
        shortcut_settings = QShortcut(QKeySequence("Ctrl+T"), self)
        shortcut_settings.activated.connect(self.toggle_settings_panel)

        shortcut_history = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_history.activated.connect(self.toggle_history_panel)

    def _pick_avatar(self, side):
        """点击头像选择本地图片"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择头像图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if filepath:
            if side == "ai1":
                self._ai1_avatar_path = filepath
                self._apply_avatar_image(self.lbl_ai1_avatar, filepath)
            else:
                self._ai2_avatar_path = filepath
                self._apply_avatar_image(self.lbl_ai2_avatar, filepath)

    def _avatar_stylesheet(self, bg_color, border_radius):
        """生成头像按钮的样式表"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: {border_radius}px;
                font-weight: bold;
                font-size: 22px;
                border: 3px solid rgba(255, 255, 255, 150);
            }}
            QPushButton:hover {{
                border: 3px solid #FFD700;
                border-radius: {border_radius}px;
            }}
        """

    def _apply_avatar_image(self, button, filepath):
        """将图片应用到头像按钮"""
        size = button.width() if button.width() > 0 else 70
        pixmap = QPixmap(filepath).scaled(
            size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        button.setText("")
        button.setIcon(QIcon(pixmap))
        button.setIconSize(pixmap.size())

    def resizeEvent(self, event):
        """窗口缩放时自适应调整各个 Overlay 部件的几何体"""
        super().resizeEvent(event)
        w, h = self.width(), self.height()

        # 视频满屏
        self.video_player.setGeometry(0, 0, w, h)

        # 顶部：占屏幕 1/5
        top_h = h // 5
        self.top_layer.setGeometry(0, 0, w, top_h)

        # 辩题居中，留出头像空间
        topic_margin = 90
        self.lbl_topic.setGeometry(topic_margin, 10, w - topic_margin * 2, top_h // 2)

        # 头像区域绝对定位在两侧
        avatar_size = min(70, top_h - 40)
        avatar_widget_h = avatar_size + 25  # 头像 + 昵称
        border_radius = avatar_size // 2

        self.lbl_ai1_avatar.setFixedSize(avatar_size, avatar_size)
        self.lbl_ai1_avatar.setStyleSheet(self._avatar_stylesheet("#2196F3", border_radius))
        self.ai1_widget.setGeometry(15, (top_h - avatar_widget_h) // 2,
                                     avatar_size + 10, avatar_widget_h)

        self.lbl_ai2_avatar.setFixedSize(avatar_size, avatar_size)
        self.lbl_ai2_avatar.setStyleSheet(self._avatar_stylesheet("#F44336", border_radius))
        self.ai2_widget.setGeometry(w - avatar_size - 25,
                                     (top_h - avatar_widget_h) // 2,
                                     avatar_size + 10, avatar_widget_h)

        # 重新应用头像图片
        if self._ai1_avatar_path:
            self._apply_avatar_image(self.lbl_ai1_avatar, self._ai1_avatar_path)
        if self._ai2_avatar_path:
            self._apply_avatar_image(self.lbl_ai2_avatar, self._ai2_avatar_path)

        # 底部字幕：占屏幕 1/7
        bot_h = h // 7
        self.bottom_layer.setGeometry(10, h - bot_h - 10, w - 20, bot_h)

    # ================= 外部弹出面板 =================

    def toggle_settings_panel(self):
        """Ctrl+T 切换设置面板（从右侧外部弹出）"""
        main_geo = self.frameGeometry()
        panel_w = 400
        panel_h = main_geo.height()
        right_x = main_geo.x() + main_geo.width()
        y = main_geo.y()

        if self._settings_visible:
            # 隐藏：滑出到右侧
            self._settings_anim = QPropertyAnimation(self.settings_panel, b"geometry")
            self._settings_anim.setDuration(300)
            self._settings_anim.setStartValue(QRect(right_x, y, panel_w, panel_h))
            self._settings_anim.setEndValue(QRect(right_x + panel_w, y, panel_w, panel_h))
            self._settings_anim.finished.connect(self.settings_panel.hide)
            self._settings_anim.start()
        else:
            # 显示：从右侧滑入
            self.settings_panel.setGeometry(right_x + panel_w, y, panel_w, panel_h)
            self.settings_panel.show()
            self._settings_anim = QPropertyAnimation(self.settings_panel, b"geometry")
            self._settings_anim.setDuration(300)
            self._settings_anim.setStartValue(QRect(right_x + panel_w, y, panel_w, panel_h))
            self._settings_anim.setEndValue(QRect(right_x, y, panel_w, panel_h))
            self._settings_anim.start()

        self._settings_visible = not self._settings_visible

    def toggle_history_panel(self):
        """Ctrl+O 切换对话记录面板（从左侧外部弹出）"""
        main_geo = self.frameGeometry()
        panel_w = 350
        panel_h = main_geo.height()
        left_x = main_geo.x()
        y = main_geo.y()

        if self._history_visible:
            # 隐藏：滑出到左侧
            self._history_anim = QPropertyAnimation(self.history_panel, b"geometry")
            self._history_anim.setDuration(300)
            self._history_anim.setStartValue(QRect(left_x - panel_w, y, panel_w, panel_h))
            self._history_anim.setEndValue(QRect(left_x - panel_w * 2, y, panel_w, panel_h))
            self._history_anim.finished.connect(self.history_panel.hide)
            self._history_anim.start()
        else:
            # 显示：从左侧滑入
            self.history_panel.setGeometry(left_x - panel_w * 2, y, panel_w, panel_h)
            self.history_panel.show()
            self._history_anim = QPropertyAnimation(self.history_panel, b"geometry")
            self._history_anim.setDuration(300)
            self._history_anim.setStartValue(QRect(left_x - panel_w * 2, y, panel_w, panel_h))
            self._history_anim.setEndValue(QRect(left_x - panel_w, y, panel_w, panel_h))
            self._history_anim.start()

        self._history_visible = not self._history_visible

    # ================= 配置与逻辑层 =================

    def _load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.settings_panel.load_config(cfg)
                    self._sync_ui_from_config(cfg)
        except Exception as e:
            self._show_subtitle(f"[警告] 读取配置失败: {e}")

    def _save_config(self):
        cfg = self.settings_panel.get_config()
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        self._sync_ui_from_config(cfg)
        self._show_subtitle("[系统] 配置已保存更改。")
        if self._settings_visible:
            self.toggle_settings_panel()

    def _sync_ui_from_config(self, cfg):
        # 刷新辩题
        topic = cfg.get("topic", "请输入辩题")
        self.lbl_topic.setText(f"🎯 {topic}")

        # 刷新名字
        ai1_name = cfg.get("ai1", {}).get("name", "AI 1")
        ai2_name = cfg.get("ai2", {}).get("name", "AI 2")
        self.lbl_ai1_name.setText(ai1_name)
        self.lbl_ai2_name.setText(ai2_name)
        # 如果没有自定义头像，在按钮上显示名字首字
        if not self._ai1_avatar_path:
            self.lbl_ai1_avatar.setText(ai1_name[:1])
        if not self._ai2_avatar_path:
            self.lbl_ai2_avatar.setText(ai2_name[:1])

        # 刷新视频(若更改)
        self.video_player.load_and_play(cfg.get("video_path", ""))

    # ================= 字幕显示（句号切换） =================

    def _show_subtitle(self, text):
        """直接在字幕区域显示文本"""
        self.bottom_layer.setText(text)

    def _on_message_start(self, name, color):
        """流式消息开始"""
        self._subtitle_buffer = ""
        self._current_speaker = name
        self._current_color = color
        self._current_message_text = ""
        # 显示说话者名称
        self.bottom_layer.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 180);
                color: {color};
                font-size: 22px;
                border: none;
                padding: 15px 20px;
                border-radius: 10px;
            }}
        """)
        self.bottom_layer.setText(f"【{name}】: ...")

    def _on_message_chunk(self, chunk):
        """流式输出：积累文本，检测句号切换字幕"""
        self._subtitle_buffer += chunk
        self._current_message_text += chunk

        # 检测句号（中文句号和英文句号）
        last_period = -1
        for i in range(len(self._subtitle_buffer) - 1, -1, -1):
            if self._subtitle_buffer[i] in ("。", ".", "！", "!", "？", "?"):
                last_period = i
                break

        if last_period >= 0:
            # 找到最后一个句号之前的最后一个完整句子的起始位置
            # 从 last_period 往前找到上一个句号
            prev_period = -1
            for i in range(last_period - 1, -1, -1):
                if self._subtitle_buffer[i] in ("。", ".", "！", "!", "？", "?"):
                    prev_period = i
                    break

            # 显示从上一个句号之后到当前句号的内容
            sentence = self._subtitle_buffer[prev_period + 1:last_period + 1].strip()
            if sentence:
                display_text = f"【{self._current_speaker}】: {sentence}"
                self.bottom_layer.setText(display_text)
        else:
            # 没有句号，显示当前所有文本
            display_text = f"【{self._current_speaker}】: {self._subtitle_buffer}"
            self.bottom_layer.setText(display_text)

    def _on_message_end(self):
        """流式消息结束：显示最后的文本，并记录到对话历史"""
        # 显示最后一句（如果有剩余未以句号结束的内容）
        remaining = self._subtitle_buffer
        if remaining:
            # 找最后一个句号之后的剩余内容
            last_period = -1
            for i in range(len(remaining) - 1, -1, -1):
                if remaining[i] in ("。", ".", "！", "!", "？", "?"):
                    last_period = i
                    break
            if last_period >= 0 and last_period < len(remaining) - 1:
                tail = remaining[last_period + 1:].strip()
                if tail:
                    self.bottom_layer.setText(
                        f"【{self._current_speaker}】: {tail}")
            elif last_period < 0:
                self.bottom_layer.setText(
                    f"【{self._current_speaker}】: {remaining}")

        # 记录到历史面板
        if self._current_message_text.strip():
            self.history_panel.append_message(
                self._current_speaker, self._current_message_text,
                self._current_color
            )

    def _on_error(self, err_text):
        self._on_message_start("错误", "#FFEB3B")
        self._on_message_chunk(f"⚠️ {err_text}")
        self._on_message_end()

    def _on_finished(self):
        self._show_subtitle("== 本场辩论已结束 ==")
        self.history_panel.append_message("系统", "本场辩论已结束", "#FFFFFF")
        self.settings_panel.btn_start.setEnabled(True)

    # ================= 辩论控制 =================

    def start_debate(self):
        cfg = self.settings_panel.get_config()
        self._sync_ui_from_config(cfg)
        self.history_panel.clear_history()

        if self.engine and self.engine.isRunning():
            self.engine.stop()

        self.engine = DebateEngine(cfg)
        self.engine.message_start_sig.connect(self._on_message_start)
        self.engine.message_chunk_sig.connect(self._on_message_chunk)
        self.engine.message_end_sig.connect(self._on_message_end)
        self.engine.error_sig.connect(self._on_error)
        self.engine.finished_sig.connect(self._on_finished)
        self.engine.start()

        self.settings_panel.btn_start.setEnabled(False)
        if self._settings_visible:
            self.toggle_settings_panel()

    def stop_debate(self):
        if self.engine and self.engine.isRunning():
            self.engine.stop()
            self._on_message_start("系统", "#FFEB3B")
            self._on_message_chunk("\n[收到停止指令，即将终止...]")
            self._on_message_end()
