import requests


class AIClient:
    def __init__(self, api_url, api_key, model_name):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name

    def chat(self, system_prompt, history):
        """调用通用Chat Completions接口生成对话"""
        if not self.api_url or not self.api_key:
            return "(配置缺失，进入本地测试模式回复...)"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 组装消息列表
        messages = [{"role": "system", "content": system_prompt}]
        for entry in history:
            messages.append({"role": entry["role"], "content": entry["content"]})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.8
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            # 解析通用格式返回结果
            return data.get("choices", [{}])[0].get("message", {}).get("content", "解析失败")
        except Exception as e:
            raise Exception(f"API请求异常: {str(e)}")