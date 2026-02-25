import os
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.responses.response_completed_event import ResponseCompletedEvent
from volcenginesdkarkruntime.types.responses.response_text_delta_event import ResponseTextDeltaEvent


class AIClient:
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self.previous_response_id = None  # 用于管理当前AI的上下文记忆

        if self.api_key:
            self.client = Ark(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=self.api_key
            )

    def chat_stream(self, input_text):
        """流式调用 Responses API 并管理上下文 ID"""
        if not self.client or not self.model_name:
            yield "(配置缺失...)"
            return

        kwargs = {
            "model": self.model_name,
            "input": input_text,
            "stream": True
        }

        # 如果有上一次请求积累的 ID，直接传入，模型会自动结合先前的对话记忆
        if self.previous_response_id:
            kwargs["previous_response_id"] = self.previous_response_id

        try:
            response = self.client.responses.create(**kwargs)

            # 解析流式事件
            for event in response:
                if isinstance(event, ResponseTextDeltaEvent):
                    # 只要产生新文本就立刻 yield 给外部
                    yield event.delta
                elif isinstance(event, ResponseCompletedEvent):
                    # 对话回合结束，保存该 ID 以供下一轮继承
                    if hasattr(event.response, 'id'):
                        self.previous_response_id = event.response.id

        except Exception as e:
            yield f"\n[请求异常: {str(e)}]"