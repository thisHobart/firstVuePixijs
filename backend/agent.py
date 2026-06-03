import asyncio
import inspect
import random
import os
from typing import List, Dict, Any
import json
import re
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from characters.personas import CHARACTER_PERSONAS, DEFAULT_PERSONA

try:
    from autogen_ext.models.ollama import OllamaChatCompletionClient
except ImportError:
    OllamaChatCompletionClient = None

load_dotenv()

# —— 读取模型配置 ——
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").strip().lower()
MODEL = os.getenv("MODEL")
API_KEY = os.getenv("OPENAI_API_KEY")          # 你的第三方 key
BASE_URL = os.getenv("OPENAI_API_URL")        # 你的第三方 base_url（OpenAI 兼容）

if not MODEL:
    raise ValueError("错误: 未找到 MODEL。请在 .env 中设置你的模型名称。")
if MODEL_PROVIDER not in {"openai", "ollama"}:
    raise ValueError("错误: MODEL_PROVIDER 只支持 openai 或 ollama。")
if MODEL_PROVIDER == "openai":
    if not API_KEY:
        raise ValueError("错误: 未找到 OPENAI_API_KEY（或 LLM_API_KEY）。请在 .env 中设置你的第三方平台密钥。")
    if not BASE_URL:
        raise ValueError("错误: 未找到 OPENAI_BASE_URL（或 LLM_API_BASE）。请在 .env 中设置你的第三方接口 base_url。")
if MODEL_PROVIDER == "ollama" and OllamaChatCompletionClient is None:
    raise ValueError("错误: 当前环境缺少 autogen_ext.models.ollama，请确认已安装支持 Ollama 的 autogen-ext。")

def _normalize_base(url: str | None):
    if not url:
        return None
    return url.rstrip("/")  # 避免双斜杠；一般需要以 /v1 结尾的完整地址

def _create_model_client():
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
    )

class AgentManager:
    """Create isolated Agent instances for each model call."""

    def __init__(self):
        max_concurrent = int(os.getenv("DIALOGUE_MAX_CONCURRENT", "5"))
        self._dialogue_semaphore = asyncio.Semaphore(max_concurrent)

        print(
            f"AgentManager initialized with {MODEL_PROVIDER} model: {MODEL}; "
            f"max concurrent dialogue calls: {max_concurrent}"
        )

    def _create_assistant(self, character: str) -> tuple[AssistantAgent, Any]:
        persona = CHARACTER_PERSONAS.get(character, DEFAULT_PERSONA)
        model_client = _create_model_client()
        assistant = AssistantAgent(
            name=character,
            model_client=model_client,
            system_message=persona,
        )
        return assistant, model_client

    async def _close_model_client(self, model_client: Any) -> None:
        close = getattr(model_client, "close", None)
        if not callable(close):
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    async def chat_once(self, character: str, user_text: str) -> str:
        # —— 调优参数（可按需调大/调小） ——
        max_attempts = 3                 # 最大重试次数（总共尝试 3 次）
        base_delay  = 0.8                # 初始退避（秒）
        per_req_timeout = 300             # 单次请求超时（秒）
        transient_codes = (429, 502, 503, 504)

        async def _call_once():
            assistant, model_client = self._create_assistant(character)
            try:
                return await assistant.run(task=user_text)
            finally:
                await self._close_model_client(model_client)

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
                async with self._dialogue_semaphore:
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

def _build_agent_task(trigger_text: str, story_context: Dict[str, Any] | None) -> str:
    if not story_context:
        return trigger_text

    current_node = story_context.get("currentNodeId", "")
    node_title = story_context.get("title", "")
    target_character = story_context.get("targetCharacter", "")
    speaking_order = story_context.get("speakingOrder") or []
    completed_nodes = story_context.get("completedNodes") or []
    current_stage = story_context.get("currentStage") or {}
    case_truth = story_context.get("caseTruth") or {}
    evidence_chain = story_context.get("evidenceChain") or {}
    npc_profiles = story_context.get("npcProfiles") or {}
    interrogation_state = story_context.get("interrogationState") or {}
    interruption_rules = story_context.get("interruptionRules") or []
    scene_memory = story_context.get("sceneMemory") or {}
    npc_memory = story_context.get("npcMemory") or {}
    available_next_nodes = story_context.get("availableNextNodes") or []
    if not isinstance(available_next_nodes, list):
        available_next_nodes = []
    if not isinstance(completed_nodes, list):
        completed_nodes = []

    return (
        "当前剧情上下文：\n"
        f"- currentNode: {current_node}\n"
        f"- title: {node_title}\n"
        f"- targetCharacter: {target_character}\n"
        f"- speakingOrder: {json.dumps(speaking_order, ensure_ascii=False)}\n"
        f"- currentStage: {json.dumps(current_stage, ensure_ascii=False)}\n"
        f"- availableNextNodes: {json.dumps(available_next_nodes, ensure_ascii=False)}\n"
        f"- completedNodes: {json.dumps(completed_nodes, ensure_ascii=False)}\n"
        f"- caseTruth: {json.dumps(case_truth, ensure_ascii=False)}\n"
        f"- evidenceChain: {json.dumps(evidence_chain, ensure_ascii=False)}\n"
        f"- npcProfiles: {json.dumps(npc_profiles, ensure_ascii=False)}\n"
        f"- interrogationState: {json.dumps(interrogation_state, ensure_ascii=False)}\n"
        f"- interruptionRules: {json.dumps(interruption_rules, ensure_ascii=False)}\n"
        f"- sceneMemory: {json.dumps(scene_memory, ensure_ascii=False)}\n"
        f"- npcMemory: {json.dumps(npc_memory, ensure_ascii=False)}\n"
        "规则：free_interrogation是乾清宫同场景多人审问，所有NPC都在场，"
        "你能听见sceneMemory.recentTurns中的公开对话，即使玩家刚才不是直接对你说话。"
        "你必须结合当前阶段、已获得证据、NPC隐瞒信息和interrogationState判断自己是否应答或插话。"
        "不得让NPC说出自己不知道的信息；被列入hides的信息只能在触发条件满足且符合当前阶段时谨慎透露。"
        "普通对话或对峙不等于剧情推进。只有当玩家本轮发言产生新证据、明显说服当前NPC、"
        "或触发与你角色相关的关键状态变化时，才可以建议nextNode。"
        "如果当前对话不足以推动剧情，nextNode必须返回'end'。"
        "nextNode必须从availableNextNodes中选择，且不能是completedNodes中已经完成过的节点。"
        "未形成证据链前不得建议final_judgement。"
        "不要编造availableNextNodes以外的剧情节点，也不要反复建议已经触发过的同一剧情。\n"
        "你必须参考sceneMemory.recentTurns，保持和前文说法一致，不能忘记自己或其他NPC刚才说过的话。"
        "如果你发现本轮对话触发了与你角色相关的状态变化，可以在stateUpdates中建议更新。"
        "允许的stateUpdates字段：minister可建议ministerContradictionFound、ministerLedgerSuppressed；"
        "maid可建议maidHandwritingHint；eunuch可建议eunuchEntryRecord；emperor可建议emperorTrust。"
        "允许的evidenceUpdates证据ID：bloodLetter、handwritingHint、palaceEntryRecord、ledgerClue、borderArmyLink。"
        "只有信息来源与当前NPC知道的信息匹配时，才可以新增证据。"
        "当玩家只拿血书直接逼皇帝查皇子，应判定证据不足；当玩家串联笔迹、出入记录、户部副账、边军粮草时，才允许推进。\n"
        f"当前触发文本：{trigger_text}"
    )


def _normalize_favorability_change(value: Any) -> int:
    try:
        delta = int(value)
    except (TypeError, ValueError):
        return 0
    return max(-5, min(5, delta))


def _normalize_next_node(value: Any, story_context: Dict[str, Any] | None) -> str:
    if not isinstance(value, str) or not value or value == "end":
        return "end"
    if not story_context:
        return value

    available_next_nodes = story_context.get("availableNextNodes") or []
    completed_nodes = story_context.get("completedNodes") or []
    if not isinstance(available_next_nodes, list):
        available_next_nodes = []
    if not isinstance(completed_nodes, list):
        completed_nodes = []

    if value not in available_next_nodes or value in completed_nodes:
        return "end"
    return value


async def generate_dialogue(
    character: str,
    conversation_history: list,
    story_context: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
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
        task = _build_agent_task(last_message, story_context)
        text = await agent_manager.chat_once(character, task)
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
                item.setdefault("stateUpdates", {})
                item.setdefault("evidenceUpdates", [])
                item["nextNode"] = _normalize_next_node(
                    item.get("nextNode"),
                    story_context,
                )
                item["favorabilityChange"] = _normalize_favorability_change(
                    item.get("favorabilityChange")
                )
                if not isinstance(item["stateUpdates"], dict):
                    item["stateUpdates"] = {}
                if not isinstance(item["evidenceUpdates"], list):
                    item["evidenceUpdates"] = []
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
