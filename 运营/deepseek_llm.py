# deepseek_llm.py
from pandasai.llm import LLM
import requests
import json

class DeepseekLLM(LLM):
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.1,
        max_tokens: int = 4096
    ):
        # 移除父类初始化参数
        super().__init__()  # 不再传递 api_key 和 model
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.last_prompt = None

    def call(self, instruction: str, context: str = None, **kwargs) -> str:
        """
        调用 Deepseek 模型的 API 以获取响应。

        :param instruction: 发送给模型的指令，通常是用户的问题或请求。
        :param context: 可选的上下文信息，当前未使用。
        :param kwargs: 其他可选参数，当前未使用。
        :return: 模型返回的响应内容。
        """
        # 将instruction转换为字符串，确保可以JSON序列化
        instruction_str = str(instruction)
        # 记录最后一次使用的提示信息
        self.last_prompt = instruction_str
        # 设置请求头，指定内容类型为 JSON，并添加 API 密钥进行身份验证
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # 构建请求数据，包含模型名称、用户消息、温度和最大生成令牌数
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": instruction_str}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        # 发送 POST 请求到 Deepseek API
        response = requests.post(self.base_url, headers=headers, json=data)
        # 检查响应状态码，如果不是 200 则抛出异常
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, {response.text}")

        # 解析响应的 JSON 数据并返回模型生成的内容
        return response.json()["choices"][0]["message"]["content"]

    @property
    def type(self) -> str:
        return "deepseek-chat"
