"""Shared AutoGen agent utilities."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import random
import re
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

try:
    from autogen_ext.models.ollama import OllamaChatCompletionClient
except ImportError:
    OllamaChatCompletionClient = None


load_dotenv()

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").strip().lower()
MODEL = os.getenv("MODEL")
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_API_URL")

if not MODEL:
    raise ValueError("错误: 未找到 MODEL。请在 .env 中设置你的模型名称。")
if MODEL_PROVIDER not in {"openai", "ollama"}:
    raise ValueError("错误: MODEL_PROVIDER 只支持 openai 或 ollama。")
if MODEL_PROVIDER == "openai":
    if not API_KEY:
        raise ValueError("错误: 未找到 OPENAI_API_KEY。请在 .env 中设置你的第三方平台密钥。")
    if not BASE_URL:
        raise ValueError("错误: 未找到 OPENAI_API_URL。请在 .env 中设置你的第三方接口 base_url。")
if MODEL_PROVIDER == "ollama" and OllamaChatCompletionClient is None:
    raise ValueError("错误: 当前环境缺少 autogen_ext.models.ollama，请确认已安装支持 Ollama 的 autogen-ext。")


def normalize_base_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/")


def create_model_client() -> Any:
    """Create a fresh model client for one isolated agent call."""

    if MODEL_PROVIDER == "ollama":
        return OllamaChatCompletionClient(
            model=MODEL,
            model_info={
                "family": "unknown",
                "vision": False,
                "function_calling": False,
                "json_output": True,
                "structured_output": True,
            },
        )

    return OpenAIChatCompletionClient(
        model=MODEL,
        api_key=API_KEY,
        base_url=normalize_base_url(BASE_URL),
        model_info={
            "family": "unknown",
            "vision": False,
            "function_calling": False,
            "json_output": True,
            "structured_output": True,
        },
    )


def extract_json_from_text(text: str) -> Any:
    """Parse JSON from raw text, fenced code block, or first balanced object."""

    s = text.strip()

    try:
        return json.loads(s)
    except Exception:
        pass

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, flags=re.IGNORECASE)
    if fence_match:
        return json.loads(fence_match.group(1).strip())

    start = s.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(s[start : i + 1])

    raise json.JSONDecodeError("Unable to parse JSON from text", s, 0)


class BaseAgent:
    """Base class for one-shot AutoGen AssistantAgent calls."""

    def __init__(
        self,
        name: str,
        system_message: str,
        semaphore: asyncio.Semaphore,
        timeout_seconds: int = 120,
        max_attempts: int = 3,
    ) -> None:
        self.name = name
        self.system_message = system_message
        self.semaphore = semaphore
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.base_delay = 0.8
        self.transient_codes = (429, 502, 503, 504)

    def create_assistant(self, model_client: Any) -> AssistantAgent:
        return AssistantAgent(
            name=self.name,
            model_client=model_client,
            system_message=self.system_message,
        )

    async def close_model_client(self, model_client: Any) -> None:
        close = getattr(model_client, "close", None)
        if not callable(close):
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    def is_transient_error(self, exc: Exception) -> bool:
        if isinstance(exc, asyncio.TimeoutError):
            return True
        msg = (str(exc) or "").lower()
        code_in_msg = any(
            code in msg
            for code in ["429", "502", "503", "504", "rate limit", "temporarily unavailable"]
        )
        status = getattr(exc, "status_code", None)
        return code_in_msg or (status in self.transient_codes)

    async def _call_once(self, task: str) -> Any:
        model_client = create_model_client()
        assistant = self.create_assistant(model_client)
        try:
            return await assistant.run(task=task)
        finally:
            await self.close_model_client(model_client)

    @staticmethod
    def result_to_text(result: Any) -> str:
        messages = getattr(result, "messages", None) or []
        for message in reversed(messages):
            content = getattr(message, "content", None)
            if isinstance(content, str) and content.strip():
                return content[:-9].rstrip() if content.rstrip().endswith("TERMINATE") else content
        return "（无有效回复）"

    async def run_text(self, task: str, fallback: str) -> str:
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                async with self.semaphore:
                    result = await asyncio.wait_for(
                        self._call_once(task),
                        timeout=self.timeout_seconds,
                    )
                return self.result_to_text(result)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_attempts and self.is_transient_error(exc):
                    delay = self.base_delay * (2 ** (attempt - 1))
                    delay = delay * (0.85 + 0.3 * random.random())
                    await asyncio.sleep(delay)
                    continue
                break

        print(f"[{self.name}] failed after {self.max_attempts} attempts: {last_error!r}")
        return fallback
