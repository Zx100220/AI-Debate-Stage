import json
import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QPushButton, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QTimer
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

from core.video_player import VideoPlayer
from core.debate_engine import DebateEngine
from ui.settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 竖屏手机尺寸比例近似
        self.setMinimumSize(540, 960)
        self.setWindowTitle("AI 辩论台")
        self.setStyleSheet("background-color: black;")

        self.engine = None
        self.panel_visible = False
        self.config_file = "config.json"

        self._init_ui()
        self._load_config()

    def _init_ui(self):
        # 0. 底层视频播放器
        self.video_player = VideoPlayer(self)

        # ----------- 绝对定位的浮层 -----------
        # 1. 顶部区域：辩题和头像
        self.top_layer = QWidget(self)
        self.top_layer.setStyleSheet("background-color: rgba(0, 0, 0, 150);")

        self.lbl_topic = QLabel("未设置辩题", self.top_layer)
        self.lbl_topic.setAlignment(Qt.AlignCenter)
        self.lbl_topic.setStyleSheet("color: white; font-weight: bold; font-size: 24px; padding: 10px;")

        self.lbl_ai1_avatar = self._create_avatar("正方", self.top_layer, is_left=True)
        self.lbl_ai2_avatar = self._create_avatar("反方", self.top_layer, is_left=False)

        # 2. 底部字幕区域
        self.bottom_layer = QTextEdit(self)
        self.bottom_layer.setReadOnly(True)
        # 去除边框与背景，纯白相近色字体
        self.bottom_layer.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 180);
                color: #FFFFFF;
                font-size: 22px;
                border: none;
                padding: 15px;
            }
            QScrollBar:vertical { width: 0px; }
        """)

        # 3. 控制面板 (初始化在右侧画面外)
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.btn_save.clicked.connect(self._save_config)
        self.settings_panel.btn_start.clicked.connect(self.start_debate)
        self.settings_panel.btn_stop.clicked.connect(self.stop_debate)

        # 浮动设置按钮
        self.btn_toggle_panel = QPushButton("⚙ 设置", self)
        self.btn_toggle_panel.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_panel.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 200);
                color: white; border-radius: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(100, 100, 100, 250); }
        """)
        self.btn_toggle_panel.clicked.connect(self.toggle_settings_panel)

    def _create_avatar(self, text, parent, is_left=True):
        lbl = QLabel(text, parent)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            border-radius: 35px;
            font-weight: bold;
            font-size: 16px;
        """)
        if not is_left:
            lbl.setStyleSheet(lbl.styleSheet().replace("#2196F3", "#F44336"))
        return lbl

    def resizeEvent(self, event):
        """窗口缩放时自适应调整各个Overlay部件的几何体"""
        super().resizeEvent(event)
        w, h = self.width(), self.height()

        # 视频满屏
        self.video_player.setGeometry(0, 0, w, h)

        # 顶部：占屏幕 1/6
        top_h = h // 6
        self.top_layer.setGeometry(0, 0, w, top_h)
        self.lbl_topic.setGeometry(0, 0, w, top_h)

        # 头像绝对定位在两侧
        avatar_size = min(70, top_h - 20)
        self.lbl_ai1_avatar.setFixedSize(avatar_size, avatar_size)
        self.lbl_ai2_avatar.setFixedSize(avatar_size, avatar_size)
        self.lbl_ai1_avatar.move(20, (top_h - avatar_size) // 2)
        self.lbl_ai2_avatar.move(w - avatar_size - 20, (top_h - avatar_size) // 2)

        # 底部字幕：占屏幕 1/6
        bot_h = h // 6
        self.bottom_layer.setGeometry(0, h - bot_h, w, bot_h)

        # 面板滑出与隐藏的动画相关数值
        self.panel_w = int(w * 0.7)  # 占屏幕约大半
        if self.panel_visible:
            self.settings_panel.setGeometry(w - self.panel_w, 0, self.panel_w, h)
        else:
            self.settings_panel.setGeometry(w, 0, self.panel_w, h)

        self.btn_toggle_panel.setGeometry(w - 70, h // 2, 80, 40)

    def toggle_settings_panel(self):
        w, h = self.width(), self.height()
        self.anim = QPropertyAnimation(self.settings_panel, b"geometry")
        self.anim.setDuration(300)

        if self.panel_visible:
            self.anim.setEndValue(QRect(w, 0, self.panel_w, h))
            self.btn_toggle_panel.setText("⚙ 设置")
        else:
            self.anim.setEndValue(QRect(w - self.panel_w, 0, self.panel_w, h))
            self.btn_toggle_panel.setText("▶ 隐藏")
            self.settings_panel.raise_()
            self.btn_toggle_panel.raise_()

        self.anim.start()
        self.panel_visible = not self.panel_visible

    # ================= 配置与逻辑层 =================

    def _load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.settings_panel.load_config(cfg)
                    self._sync_ui_from_config(cfg)
        except Exception as e:
            self.append_subtitle(f"[警告] 读取配置失败: {e}", color="red")

    def _save_config(self):
        cfg = self.settings_panel.get_config()
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        self._sync_ui_from_config(cfg)
        self.append_subtitle("[系统] 配置已保存更改。")
        self.toggle_settings_panel()

    def _sync_ui_from_config(self, cfg):
        # 刷新辩题
        self.lbl_topic.setText(cfg.get("topic", "请输入辩题"))

        # 刷新名字
        self.lbl_ai1_avatar.setText(cfg.get("ai1", {}).get("name", "AI 1")[:4])
        self.lbl_ai2_avatar.setText(cfg.get("ai2", {}).get("name", "AI 2")[:4])

        # 刷新视频(若更改)
        self.video_player.load_and_play(cfg.get("video_path", ""))

    def append_subtitle(self, text, color="white"):
        """向底部字幕区域追加内容"""
        # HTML包装，加入颜色控制
        html = f'<p style="color: {color}; margin: 5px;">{text}</p>'
        self.bottom_layer.append(html)
        self.bottom_layer.verticalScrollBar().setValue(
            self.bottom_layer.verticalScrollBar().maximum()
        )

    def start_debate(self):
        cfg = self.settings_panel.get_config()
        self._sync_ui_from_config(cfg)

        self.bottom_layer.clear()

        if self.engine and self.engine.isRunning():
            self.engine.stop()

        self.engine = DebateEngine(cfg)

        # 绑定新的流式事件信号
        self.engine.message_start_sig.connect(self._on_message_start)
        self.engine.message_chunk_sig.connect(self._on_message_chunk)
        self.engine.message_end_sig.connect(self._on_message_end)
        self.engine.error_sig.connect(self._on_error)
        self.engine.finished_sig.connect(self._on_finished)
        self.engine.start()

        self.settings_panel.btn_start.setEnabled(False)
        if self.panel_visible:
            self.toggle_settings_panel()

    def stop_debate(self):
        if self.engine and self.engine.isRunning():
            self.engine.stop()
            self._on_message_start("系统", "#FFEB3B")
            self._on_message_chunk("\n[收到停止指令，即将终止...]")
            self._on_message_end()

    def _on_message_start(self, name, color):
        """流式消息开始：输出角色的名称和排版样式"""
        cursor = self.bottom_layer.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.bottom_layer.setTextCursor(cursor)

        # 配置格式化对象
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(QFont.Bold)

        # 插入名字标签
        cursor.insertText(f"\n【{name}】: ", fmt)

        # 恢复默认正文格式(但不恢复颜色，全段保持同一着色)
        fmt.setFontWeight(QFont.Normal)
        self.bottom_layer.setCurrentCharFormat(fmt)

    def _on_message_chunk(self, chunk):
        """流式输出：依次向文本框插入碎步字符，实现打字机效果"""
        cursor = self.bottom_layer.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        # 使得滚动条实时滚动到底部
        scrollbar = self.bottom_layer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_message_end(self):
        """流式消息结束（若有特定结束需求可在此添加）"""
        pass

    def _on_error(self, err_text):
        self._on_message_start("错误", "#FFEB3B")
        self._on_message_chunk(f"⚠️ {err_text}")
        self._on_message_end()

    def _on_finished(self):
        self._on_message_start("系统", "#FFFFFF")
        self._on_message_chunk("\n\n== 本场辩论已结束 ==\n")
        self._on_message_end()
        self.settings_panel.btn_start.setEnabled(True)