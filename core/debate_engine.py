import time
from PyQt5.QtCore import QThread, pyqtSignal
from .ai_client import AIClient


class DebateEngine(QThread):
    # 更细粒度的信号，适配字幕式的逐字敲出效果
    # 开始一段消息：信号传递 (名称, 颜色色值)
    message_start_sig = pyqtSignal(str, str)
    # 消息的文本碎片：信号传递 (碎片文本)
    message_chunk_sig = pyqtSignal(str)
    # 一段消息结束
    message_end_sig = pyqtSignal()

    error_sig = pyqtSignal(str)
    finished_sig = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False

    def run(self):
        self.is_running = True
        try:
            ai1_cfg = self.config.get("ai1", {})
            ai2_cfg = self.config.get("ai2", {})

            # 初始化两名辩手
            client1 = AIClient(ai1_cfg.get("api_key"), ai1_cfg.get("model_name"))
            client2 = AIClient(ai2_cfg.get("api_key"), ai2_cfg.get("model_name"))

            topic = self.config.get("topic", "未知辩题")
            rounds = int(self.config.get("rounds", 3))

            last_reply = ""

            for i in range(rounds):
                if not self.is_running: break

                # ---- AI 1 回合 ----
                self.message_start_sig.emit("系统", "#FFFFFF")
                self.message_chunk_sig.emit(f"\n\n--- 第 {i + 1} 轮辩论 ---\n")
                self.message_end_sig.emit()

                # 第一轮加入角色设定，后续轮次因为有 previous_response_id，只需告知对方说了什么
                if i == 0:
                    prompt_1 = f"当前辩题：{topic}\n你的角色设定是：{ai1_cfg.get('style', '')}\n请作为正方开场发表观点。"
                else:
                    prompt_1 = f"对方辩友刚才反驳说：“{last_reply}”\n请继续反驳对方。"

                self.message_start_sig.emit(ai1_cfg.get("name", "正方"), "#80D8FF")
                last_reply = ""
                # 流式不断拉取片段并发送给UI
                for chunk in client1.chat_stream(prompt_1):
                    if not self.is_running: break
                    last_reply += chunk
                    self.message_chunk_sig.emit(chunk)
                self.message_end_sig.emit()

                time.sleep(1.5)
                if not self.is_running: break

                # ---- AI 2 回合 ----
                if i == 0:
                    prompt_2 = f"当前辩题：{topic}\n你的角色设定是：{ai2_cfg.get('style', '')}\n对方正方开场说道：“{last_reply}”。\n请作为反方进行反驳。"
                else:
                    prompt_2 = f"对方辩友刚才反驳说：“{last_reply}”\n请继续反驳对方。"

                self.message_start_sig.emit(ai2_cfg.get("name", "反方"), "#FF8A80")
                last_reply = ""
                for chunk in client2.chat_stream(prompt_2):
                    if not self.is_running: break
                    last_reply += chunk
                    self.message_chunk_sig.emit(chunk)
                self.message_end_sig.emit()

                time.sleep(1.5)

        except Exception as e:
            self.error_sig.emit(str(e))
        finally:
            self.is_running = False
            self.finished_sig.emit()

    def stop(self):
        self.is_running = False