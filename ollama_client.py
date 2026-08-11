"""Ollama 本地模型调用客户端"""
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, model: str = "qwen2.5-coder:32b", host: str = "http://localhost:11434",
                 temperature: float = 0.1, max_tokens: int = 4096):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _api_url(self, path: str) -> str:
        return f"{self.host}/api/{path}"

    def chat(self, messages: list[dict], stream: bool = False) -> str:
        payload = {
            "model": self.model, "messages": messages, "stream": stream,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        resp = requests.post(self._api_url("chat"), json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        payload = {
            "model": self.model, "prompt": prompt, "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        if system:
            payload["system"] = system
        resp = requests.post(self._api_url("generate"), json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["response"]

    def list_models(self) -> list:
        resp = requests.get(self._api_url("tags"), timeout=10)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]

    def check_available(self) -> bool:
        try:
            models = self.list_models()
            if self.model not in models:
                logger.error(f"模型 {self.model} 未安装，可用模型: {models}")
                return False
            return True
        except requests.RequestException:
            logger.error("Ollama 服务不可用")
            return False
