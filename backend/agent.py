import asyncio
import random
import os
from typing import List, Dict, Any
import json
import re
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()

# —— 读取第三方（OpenAI 兼容）环境变量 ——
MODEL   = os.getenv("MODEL")
API_KEY = os.getenv("OPENAI_API_KEY")          # 你的第三方 key
BASE_URL = os.getenv("OPENAI_API_URL")        # 你的第三方 base_url（OpenAI 兼容）
TEMPERATURE = 0.7

if not API_KEY:
    raise ValueError("错误: 未找到 OPENAI_API_KEY（或 LLM_API_KEY）。请在 .env 中设置你的第三方平台密钥。")
if not BASE_URL:
    raise ValueError("错误: 未找到 OPENAI_BASE_URL（或 LLM_API_BASE）。请在 .env 中设置你的第三方接口 base_url。")
if not MODEL:
    raise ValueError("错误: 未找到 OPENAI_MODEL。请在 .env 中设置你的模型名称。")

def _normalize_base(url: str | None):
    if not url:
        return None
    return url.rstrip("/")  # 避免双斜杠；一般需要以 /v1 结尾的完整地址

character_personas = {
    "emperor": (
        "你是一位威言而睿智的古代中国皇帝。"
        "你的话语简洁、有力，充满威严。"
        "你要根据玩家的对话，分析其意图和礼仪，然后决定你对玩家的好感度变化。"
        "请以JSON格式返回，包含'speaker', 'text', 'nextNode'和'favorabilityChange'。"
        "favorabilityChange是一个整数，可以是-1（好感度下降），0（不变），或1（好感度上升）。"
        "例如：{'speaker': 'emperor', 'text': '...', 'nextNode': 'end', 'favorabilityChange': 1}"
    ),
}

class AgentManager:
    """管理和缓存 Agent 实例以提高性能。"""

    def __init__(self):
        self._assistant_agents: Dict[str, AssistantAgent] = {}

        # ❶ 不阻塞的输入函数
        def _no_input(prompt: str = "") -> str:
            return ""

        self._user_proxy_agent = UserProxyAgent(
            name="user_proxy",
            description="A programmatic user (no interactive input).",
            input_func=_no_input,
        )

        # ❷ 构造第三方 OpenAI 兼容的“模型客户端”（替代旧 llm_config）
        # 注：不同小版本字段名可能是 default_request_kwargs / default_params / default_request_params
        # 若你的小版本报未知参数，把 temperature 挪到 chat_once 里的请求参数传递（见下方注释）。
        self._model_client = OpenAIChatCompletionClient(
            model=MODEL,
            api_key=API_KEY,
            base_url=_normalize_base(BASE_URL),
            model_info={
                # 模型家族：可用枚举，也可用字符串 "unknown"
                # 若你确知是 R1/LLAMA/CLAUDE 等系列，可换成对应常量；不确定就用 "unknown"
                "family": "unknown",  # 或 ModelFamily.R1 / ModelFamily.GPT_4O / ...

                # 下面这些布尔项按你的第三方实际能力填写：
                "vision": False,  # 是否支持图像输入
                "function_calling": False,  # 是否支持函数/工具调用（OpenAI-style tool calling）
                "json_output": True,  # 是否支持 JSON 模式（非结构化 JSON）
                "structured_output": True,  # 是否支持“结构化输出”（严格 schema）
            },

            # —— 默认生成参数（若你的小版本不支持此字段，删掉它） ——
            default_request_kwargs={
                "temperature": TEMPERATURE,
                # 若第三方支持 seed，可加：
                # "seed": 42,
            },
            # 如果第三方需要额外头部：
            # extra_headers={"X-My-Vendor": "foo"},
        )

        print("AgentManager initialized.")

    def get_assistant(self, character: str) -> AssistantAgent:
        if character not in self._assistant_agents:
            print(f"Creating new assistant agent for: {character}")
            persona = character_personas.get(character, "你是一个通用的NPC。")
            self._assistant_agents[character] = AssistantAgent(
                name=character,
                model_client=self._model_client,   # ★ 用 model_client，替代 llm_config
                system_message=persona,
                # 如需流式：model_client_stream=True,
            )
        return self._assistant_agents[character]

    def get_user_proxy(self) -> UserProxyAgent:
        return self._user_proxy_agent

    async def chat_once(self, character: str, user_text: str) -> str:
        assistant = self.get_assistant(character)

        # —— 调优参数（可按需调大/调小） ——
        max_attempts = 3                 # 最大重试次数（总共尝试 3 次）
        base_delay  = 0.8                # 初始退避（秒）
        per_req_timeout = 30             # 单次请求超时（秒）
        transient_codes = (429, 502, 503, 504)

        async def _call_once():
            # 如你的客户端没设默认温度，可在 request_kwargs 传；否则留空
            return await assistant.run(
                task=user_text,
                # request_kwargs={"temperature": 0.7}
            )

        def _is_transient(exc: Exception) -> bool:
            # 兼容不同异常形态做“弱判定”
            msg = (str(exc) or "").lower()
            code_in_msg = any(code in msg for code in ["429", "502", "503", "504", "rate limit", "temporarily unavailable"])
            status = getattr(exc, "status_code", None)
            return code_in_msg or (status in transient_codes)

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                # ① 单次调用加超时，避免卡住事件循环
                result = await asyncio.wait_for(_call_once(), timeout=per_req_timeout)

                # ② 解析消息：从后往前找可展示文本
                msgs = getattr(result, "messages", None) or []
                for m in reversed(msgs):
                    content = getattr(m, "content", None)
                    if isinstance(content, str) and content.strip():
                        return content[:-9].rstrip() if content.rstrip().endswith("TERMINATE") else content

                # 没拿到文本，也算“成功但无输出”
                return "（无有效回复）"

            except Exception as e:
                last_error = e
                if attempt < max_attempts and _is_transient(e):
                    # ③ 指数退避 + 抖动
                    delay = base_delay * (2 ** (attempt - 1))
                    delay = delay * (0.85 + 0.3 * random.random())  # ±15% 抖动
                    try:
                        await asyncio.sleep(delay)
                    except asyncio.CancelledError:
                        # 上游取消时，立即抛出
                        raise
                    continue
                else:
                    break  # 不可重试或已到最大次数

        # ④ 多次失败，优雅降级
        # 你可以在这里记录日志/上报监控
        print(f"[chat_once] failed after {max_attempts} attempts: {last_error!r}")
        return "（当前对话服务繁忙，请稍后再试）"



# --- 创建一个全局的 AgentManager 实例 ---
agent_manager = AgentManager()


# --- 修改 generate_dialogue 函数以使用 Manager ---
def _extract_json_from_text(text: str) -> Any:
    """Try to robustly parse a JSON object from LLM text.

    Supports raw JSON, fenced ```json blocks, or best-effort curly block extraction.
    Returns parsed JSON on success, otherwise raises json.JSONDecodeError.
    """
    s = text.strip()

    # 1) Direct JSON
    try:
        return json.loads(s)
    except Exception:
        pass

    # 2) Fenced code block ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, flags=re.IGNORECASE)
    if fence_match:
        block = fence_match.group(1).strip()
        return json.loads(block)

    # 3) Best-effort: find first {...} balanced block
    start = s.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    candidate = s[start:i+1]
                    return json.loads(candidate)

    # If all strategies fail, raise
    raise json.JSONDecodeError("Unable to parse JSON from text", s, 0)

async def generate_dialogue(character: str, conversation_history: list) -> List[Dict[str, Any]]:
    """单 Agent 一问一答：拿文本→优先解析 JSON→兜底文本"""
    try:
        # 1) 取用户的最后一句作为本轮输入
        last_message = (conversation_history[-1]["content"].strip()
                        if conversation_history and "content" in conversation_history[-1] else "")
        if not last_message:
            return [{
                "speaker": character,
                "text": "（没有可用的输入）",
                "nextNode": "end",
                "favorabilityChange": 0
            }]

        # 2) 调用新版 Autogen（封装在 AgentManager.chat_once 内）
        #    这里返回的是“模型最终可展示的文本”
        text = await agent_manager.chat_once(character, last_message)
        text = (text or "").strip()

        # 3) 优先解析 JSON（支持 ```json fenced block、原始 JSON、首个 {...} 片段）
        responses: List[Dict[str, Any]] = []
        parsed_ok = False
        try:
            data = _extract_json_from_text(text)
            # 统一成 list[dict]
            items: List[Dict[str, Any]] = []
            if isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = [d for d in data if isinstance(d, dict)]

            for item in items:
                item.setdefault("speaker", character)
                item.setdefault("text", "")
                item.setdefault("nextNode", "end")
                item.setdefault("favorabilityChange", 0)
                if isinstance(item["text"], str):
                    responses.append(item)

            parsed_ok = len(responses) > 0
        except json.JSONDecodeError:
            parsed_ok = False

        # 4) 兜底文本（避免回显用户原话）
        if not parsed_ok:
            if text and text != last_message:
                responses = [{
                    "speaker": character,
                    "text": text,
                    "nextNode": "end",
                    "favorabilityChange": 0
                }]
            else:
                responses = [{
                    "speaker": character,
                    "text": "……",
                    "nextNode": "end",
                    "favorabilityChange": 0
                }]

        try:
            print("Agent responses:", json.dumps(responses, ensure_ascii=False))
        except Exception:
            pass

        return responses

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return [{
            "speaker": "system",
            "text": f"抱歉，调用AI时出现错误: {e}",
            "nextNode": "end",
            "favorabilityChange": 0,
        }]

