import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

class LLMClient:
    """
    DashScope (通义千问) OpenAI-兼容接口封装
    必需环境变量:
      - DASHSCOPE_API_KEY
    可选:
      - DASHSCOPE_BASE_URL (默认北京: https://dashscope.aliyuncs.com/compatible-mode/v1)
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing DASHSCOPE_API_KEY")

        base_url = base_url or os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, model: str, messages: List[Dict[str, Any]], temperature: float = 0.0) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

class LLMClient:
    """
    DashScope (通义千问) OpenAI-兼容接口封装
    必需环境变量:
      - DASHSCOPE_API_KEY
    可选:
      - DASHSCOPE_BASE_URL (默认北京: https://dashscope.aliyuncs.com/compatible-mode/v1)
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing DASHSCOPE_API_KEY")

        base_url = base_url or os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, model: str, messages: List[Dict[str, Any]], temperature: float = 0.0) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
