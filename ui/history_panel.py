from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont


class HistoryPanel(QWidget):
    """对话记录面板，显示所有辩论对话内容"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 240); color: white; border-radius: 10px;")

        layout = QVBoxLayout(self)

        # 标题栏（标题 + 关闭按钮）
        title_layout = QHBoxLayout()
        title = QLabel("📜 对话记录")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; color: #FFD700;")
        title_layout.addWidget(title)

        self.btn_close = QPushButton("✕")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setStyleSheet(
            "QPushButton { background-color: #555; color: white; border-radius: 16px; font-size: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #D83B01; }"
        )
        title_layout.addWidget(self.btn_close)
        layout.addLayout(title_layout)

        # 对话内容显示区域
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 20, 20, 200);
                color: #FFFFFF;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
            }
            QScrollBar:vertical {
                background: #333; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #666; border-radius: 4px; min-height: 30px;
            }
        """)
        layout.addWidget(self.text_area)

        # 清除按钮
        btn_clear = QPushButton("🗑 清除记录")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(
            "padding: 8px; font-weight: bold; background-color: #555; "
            "border-radius: 5px; color: white;"
        )
        btn_clear.clicked.connect(self.clear_history)
        layout.addWidget(btn_clear)

    def append_message(self, name, text, color="#FFFFFF"):
        """追加一条对话记录"""
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 名称格式
        name_fmt = QTextCharFormat()
        name_fmt.setForeground(QColor(color))
        name_fmt.setFontWeight(QFont.Bold)
        cursor.insertText(f"\n【{name}】: ", name_fmt)

        # 内容格式
        text_fmt = QTextCharFormat()
        text_fmt.setForeground(QColor(color))
        text_fmt.setFontWeight(QFont.Normal)
        cursor.insertText(text, text_fmt)

        self.text_area.setTextCursor(cursor)
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )

    def clear_history(self):
        self.text_area.clear()
