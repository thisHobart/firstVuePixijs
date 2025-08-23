from dotenv import load_dotenv
import os
import json
from autogen import AssistantAgent, UserProxyAgent
from typing import Dict

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
        "你是一位威严而睿智的古代中国皇帝。"
        "你的话语简洁、有力，充满威严。"
        "你要根据玩家的选择，生成符合皇帝身份的回答。"
        "请以JSON格式返回，包含'speaker', 'text', 和 'choices'(如果需要)或'nextNode'。"
        "例如：{'speaker': 'emperor', 'text': '...', 'nextNode': 'end'}"
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
            max_consecutive_auto_reply=1,
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
def generate_dialogue(character: str, conversation_history: list):
    try:
        # 从 manager 获取缓存的 agent 实例
        assistant = agent_manager.get_assistant(character)
        user_proxy = agent_manager.get_user_proxy()

        # 重置 agent 内部历史，确保每次对话都是全新的
        user_proxy.reset()
        assistant.reset()

        last_message = conversation_history[-1]["content"]

        # 使用 a_initiate_chat 而不是 initiate_chat 以支持异步
        # 这里我们仍然在同步函数中调用，但在Web服务中会用线程池处理
        user_proxy.initiate_chat(
            assistant,
            message=last_message,
            # chat_history=conversation_history[:-1] # 如果需要传递完整历史
        )

        last = assistant.last_message()
        response_text = last.get("content", "") if isinstance(last, dict) else str(last)

        try:
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"speaker": character, "text": response_text, "nextNode": "end"}

    except Exception as e:
        import traceback
        print(traceback.format_exc())  # 打印详细错误以供调试
        return {
            "speaker": "system",
            "text": f"抱歉，调用AI时出现错误: {e}",
            "nextNode": "end"
        }