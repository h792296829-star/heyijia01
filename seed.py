import os
from typing import List, Dict, Any
from openai import OpenAI

class LLMClient:
    """DashScope OpenAI兼容调用：base_url 默认北京地域。"""
    def __init__(self):
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise RuntimeError("Missing DASHSCOPE_API_KEY env var")
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
