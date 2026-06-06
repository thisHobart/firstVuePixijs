"""NPC dialogue generation agent."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from characters.personas import CHARACTER_PERSONAS, DEFAULT_PERSONA
from story.retriever import retrieve_story_context

from .base import BaseAgent, extract_json_from_text


class DialogueAgent(BaseAgent):
    """Generate visible NPC dialogue only."""

    def __init__(self, character: str, semaphore: asyncio.Semaphore) -> None:
        self.character = character
        super().__init__(
            name=character,
            system_message=CHARACTER_PERSONAS.get(character, DEFAULT_PERSONA),
            semaphore=semaphore,
            timeout_seconds=300,
            max_attempts=3,
        )

    def build_task(self, trigger_text: str, story_context: Dict[str, Any] | None) -> str:
        if not story_context:
            return trigger_text

        target_character = story_context.get("targetCharacter") or self.character
        retrieval = retrieve_story_context(target_character, trigger_text, story_context)

        return (
            "当前最小剧情上下文：\n"
            f"- dynamicState: {json.dumps(retrieval['dynamicState'], ensure_ascii=False)}\n"
            f"- retrievedContext: {json.dumps(retrieval['retrievedContext'], ensure_ascii=False)}\n"
            "规则：free_interrogation是乾清宫同场景多人审问，所有NPC都在场，"
            "你能听见dynamicState.recentTurns中的公开对话，即使玩家刚才不是直接对你说话。"
            "retrievedContext是系统检索出的、当前角色可知道且本轮相关的背景，不代表你必须全部说出。"
            "你只能扮演当前NPC，不能替其他角色说话。"
            "你不能决定剧情节点，不能输出nextNode，不能更新证据或状态，不能输出好感度变化。"
            "剧情推进、证据更新和好感度变化由系统状态机与裁判Agent处理。"
            "你必须保持和前文说法一致，不要透露retrievedContext以外的隐藏真相。"
            "如果玩家证据不足或冒犯他人，可以在角色台词中自然表现后果，但不要替系统判定剧情。\n"
            f"当前触发文本：{trigger_text}"
        )

    def parse_responses(self, raw_text: str, trigger_text: str) -> List[Dict[str, Any]]:
        responses: List[Dict[str, Any]] = []
        parsed_ok = False

        try:
            data = extract_json_from_text(raw_text)
            items: List[Dict[str, Any]] = []
            if isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = [item for item in data if isinstance(item, dict)]

            for item in items:
                text = item.get("text", "")
                if isinstance(text, str):
                    speaker = item.get("speaker")
                    responses.append({
                        "speaker": speaker if isinstance(speaker, str) else self.character,
                        "text": text,
                    })

            parsed_ok = len(responses) > 0
        except json.JSONDecodeError:
            parsed_ok = False

        if parsed_ok:
            return responses

        if raw_text and raw_text != trigger_text:
            return [{"speaker": self.character, "text": raw_text}]
        return [{"speaker": self.character, "text": "……"}]

    async def generate(
        self,
        trigger_text: str,
        story_context: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        task = self.build_task(trigger_text, story_context)
        raw_text = (await self.run_text(task, "（当前对话服务繁忙，请稍后再试）")).strip()
        return self.parse_responses(raw_text, trigger_text)
