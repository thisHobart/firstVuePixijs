from dotenv import load_dotenv
import os
import json
import re
from autogen import AssistantAgent, UserProxyAgent
from typing import Dict, Any, List

load_dotenv()

# --- 配置部分保持不变 ---
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_URL")
model = os.getenv("MODEL")

if not api_key:
    raise ValueError("错误: 未找到 LLM_API_KEY（或 OPENAI_API_KEY）。请在 .env 中设置你的第三方平台密钥。")
if not api_base:
    raise ValueError("错误: 未找到 LLM_API_BASE（或 OPENAI_API_URL）。请在 .env 中设置你的第三方接口 base_url。")
if not model:
    raise ValueError("错误: 未找到 MODEL。请在 .env 中设置你的模型名称。")

llm_config = {
    "config_list": [
        {
            "model": model,
            "api_key": api_key,
            "base_url": api_base,
            "price": [0.00014, 0.00028],
        }
    ],
    "cache_seed": 42,
    "temperature": 0.7,
}

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


# --- 引入 AgentManager 设计模式 ---
class AgentManager:
    """管理和缓存 Agent 实例以提高性能。"""

    def __init__(self):
        self._assistant_agents: Dict[str, AssistantAgent] = {}
        self._user_proxy_agent = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
        )
        print("AgentManager initialized.")

    def get_assistant(self, character: str) -> AssistantAgent:
        if character not in self._assistant_agents:
            print(f"Creating new assistant agent for: {character}")
            persona = character_personas.get(character, "你是一个通用的NPC。")
            self._assistant_agents[character] = AssistantAgent(
                name=character,
                llm_config=llm_config,
                system_message=persona
            )
        return self._assistant_agents[character]

    def get_user_proxy(self) -> UserProxyAgent:
        return self._user_proxy_agent


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


def generate_dialogue(character: str, conversation_history: list) -> List[Dict[str, Any]]:
    try:
        # 从 manager 获取缓存的 agent 实例
        assistant = agent_manager.get_assistant(character)
        user_proxy = agent_manager.get_user_proxy()

        # 重置 agent 内部历史，确保每次对话都是全新的
        user_proxy.reset()
        assistant.reset()

        last_message = conversation_history[-1]["content"]

        # 使用 initiate_chat，这里在Web服务中会用线程池处理
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=last_message,
            # 传递除最后一句以外的历史辅助模型理解上下文（可选开启）
            # chat_history=conversation_history[:-1]
        )

        # -- 新逻辑：优先从所有消息中提取符合JSON规范的助手回复 --
        def _stringify_content(val: Any) -> str:
            if isinstance(val, str):
                return val
            if isinstance(val, list):
                parts = []
                for item in val:
                    if isinstance(item, dict) and isinstance(item.get('text'), str):
                        parts.append(item['text'])
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            if isinstance(val, dict):
                if isinstance(val.get('text'), str):
                    return val['text']
                try:
                    return json.dumps(val, ensure_ascii=False)
                except Exception:
                    return str(val)
            return str(val)

        parsed_json_responses: List[Dict[str, Any]] = []
        plain_fallback_responses: List[str] = []

        if chat_result.chat_history:
            for msg in chat_result.chat_history:
                role = msg.get("role") or ""
                name = msg.get("name") or msg.get("sender") or ""
                content_raw = msg.get("content", "")
                response_text = _stringify_content(content_raw)

                # 仅考虑疑似来自助手/角色本人的消息
                if not (role == "assistant" or role == character or name == character):
                    continue

                # 优先尝试解析严格的 JSON 回复
                try:
                    data = _extract_json_from_text(response_text)
                    items: List[Dict[str, Any]] = []
                    if isinstance(data, dict):
                        items = [data]
                    elif isinstance(data, list):
                        items = [d for d in data if isinstance(d, dict)]

                    for item in items:
                        item.setdefault('speaker', character)
                        item.setdefault('text', '')
                        item.setdefault('nextNode', 'end')
                        item.setdefault('favorabilityChange', 0)
                        # 丢弃没有文本的项
                        if item['text']:
                            parsed_json_responses.append(item)
                    # 成功解析则不再把该条作为纯文本fallback
                    continue
                except json.JSONDecodeError:
                    pass

                # 记录纯文本以便兜底（避免把用户输入回显）
                if response_text and response_text.strip():
                    plain_fallback_responses.append(response_text.strip())

        responses: List[Dict[str, Any]] = []
        if parsed_json_responses:
            responses = parsed_json_responses
        else:
            # 尝试使用最后一条非空文本作为兜底，但避免回显用户的最后一句
            last_user_msg = conversation_history[-1]["content"] if conversation_history else ""
            for text in plain_fallback_responses:
                if text == last_user_msg:
                    continue
                responses.append({
                    "speaker": character,
                    "text": text,
                    "nextNode": "end",
                    "favorabilityChange": 0
                })

        # 调试日志：便于与前端核对实际返回
        try:
            print("Agent responses:", json.dumps(responses, ensure_ascii=False))
        except Exception:
            pass

        return responses

    except Exception as e:
        import traceback
        print(traceback.format_exc())  # 打印详细错误以供调试
        # 始终返回列表，保持API响应一致
        return [
            {
                "speaker": "system",
                "text": f"抱歉，调用AI时出现错误: {e}",
                "nextNode": "end",
                "favorabilityChange": 0,
            }
        ]
