from volcenginesdkarkruntime import Ark


class AIClient:
    def __init__(self, api_url, api_key, model_name):
        # 官方 SDK 会自动处理内部的接口地址，所以此处的 api_url 参数我们可以忽略
        self.api_key = api_key
        self.model_name = model_name
        self.client = None

        # 初始化 SDK 客户端
        if self.api_key:
            self.client = Ark(api_key=self.api_key)

    def chat(self, system_prompt, history):
        """调用官方 volces SDK 接口生成对话"""
        if not self.client or not self.model_name:
            return "(配置缺失，进入本地测试模式回复...)"

        # 组装消息列表 (System Prompt + 历史对话)
        messages = [{"role": "system", "content": system_prompt}]
        for entry in history:
            messages.append({"role": entry["role"], "content": entry["content"]})

        try:
            # 调用 SDK completions 接口
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )

            # 解析最终的文本内容并返回
            return completion.choices[0].message.content

        except Exception as e:
            raise Exception(f"火山引擎请求异常: {str(e)}")