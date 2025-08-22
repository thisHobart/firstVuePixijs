import autogen
from dotenv import load_dotenv
import os
import json

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL", "gpt-4")

# Check if the API key is set
if not api_key or api_key == "your_api_key_here":
    raise ValueError("错误: OPENAI_API_KEY 未在 .env 文件中设置。请添加您的 API 密钥后重试。")
else:
    config_list = [
        {
            "model": model,
            "api_key": api_key,
        }
    ]

llm_config = {
    "config_list": config_list,
    "cache_seed": 42,
    "temperature": 0.7,
}

character_personas = {
    "emperor": "你是一位威严而睿智的古代中国皇帝。你的话语简洁、有力，充满威严。你要根据玩家的选择，生成符合皇帝身份的回答。请以JSON格式返回，包含'speaker', 'text', 和 'choices' (如果需要) 或 'nextNode'。例如：{'speaker': 'emperor', 'text': '...', 'nextNode': 'end'}",
    # Add other character personas here
}

def generate_dialogue(character, conversation_history):
    persona = character_personas.get(character, "你是一个通用的NPC。")

    assistant = autogen.AssistantAgent(
        name=character,
        llm_config=llm_config,
        system_message=persona
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
    )

    # Convert conversation history to a format autogen understands
    chat_history = []
    for msg in conversation_history:
        chat_history.append({"role": "user" if msg['role'] == 'player' else 'assistant', "content": msg['content']})

    # The last message from the player is the one we want the assistant to respond to
    last_message = chat_history[-1]['content']

    user_proxy.initiate_chat(
        assistant,
        message=last_message,
        clear_history=True # Start fresh for each turn
    )

    # The response is the last message from the assistant
    response_text = assistant.last_message()["content"]

    try:
        # The prompt asks the LLM to return JSON, so we parse it
        response_json = json.loads(response_text)
        return response_json
    except json.JSONDecodeError:
        # If the LLM fails to return valid JSON, wrap it in the expected structure
        return {"speaker": character, "text": response_text, "nextNode": "end"}
