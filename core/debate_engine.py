import time
from PyQt5.QtCore import QThread, pyqtSignal
from .ai_client import AIClient


class DebateEngine(QThread):
    # 信号定义：名字, 消息内容 (方便UI做不同样式的区分)
    new_message_sig = pyqtSignal(str, str)
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

            client1 = AIClient(ai1_cfg.get("api_url"), ai1_cfg.get("api_key"), ai1_cfg.get("model_name"))
            client2 = AIClient(ai2_cfg.get("api_url"), ai2_cfg.get("api_key"), ai2_cfg.get("model_name"))

            topic = self.config.get("topic", "未知辩题")
            rounds = int(self.config.get("rounds", 3))

            # 根据风格和辩题构造系统指令
            system1 = f"当前辩题：{topic}\n你的角色设定是：{ai1_cfg.get('style', '')}\n请根据对方发言进行反驳，字数控制在50字以内，像字幕对话一样简练。"
            system2 = f"当前辩题：{topic}\n你的角色设定是：{ai2_cfg.get('style', '')}\n请根据对方发言进行反驳，字数控制在50字以内，像字幕对话一样简练。"

            history1 = []
            history2 = []

            for i in range(rounds):
                if not self.is_running: break

                # ---- AI 1 回合 ----
                self.new_message_sig.emit("系统", f"--- 第 {i + 1} 轮辩论 ---")

                # 第一轮让AI 1开场，不带前文，后续带上对方的反驳
                reply1 = client1.chat(system1, history1)
                if not self.is_running: break
                self.new_message_sig.emit(ai1_cfg.get("name", "AI 1"), reply1)

                # 双边维护上下文
                history1.append({"role": "assistant", "content": reply1})
                history2.append({"role": "user", "content": f"对方发言说：{reply1}"})

                time.sleep(2)  # 延时，保证观看体验
                if not self.is_running: break

                # ---- AI 2 回合 ----
                reply2 = client2.chat(system2, history2)
                if not self.is_running: break
                self.new_message_sig.emit(ai2_cfg.get("name", "AI 2"), reply2)

                history2.append({"role": "assistant", "content": reply2})
                history1.append({"role": "user", "content": f"对方发言说：{reply2}"})

                time.sleep(2)

        except Exception as e:
            self.error_sig.emit(str(e))
        finally:
            self.is_running = False
            self.finished_sig.emit()

    def stop(self):
        self.is_running = False