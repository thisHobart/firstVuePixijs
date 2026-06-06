"""Dialogue orchestration entrypoint.

This module is intentionally kept as a compatibility facade for main.py.
Concrete AutoGen agents live under backend/agents/.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

from agents.affection_judge_agent import AffectionJudgeAgent
from agents.dialogue_agent import DialogueAgent
from agents.input_guard_agent import InputGuardAgent
from story.progress import evaluate_story_progress


class AgentManager:
    """Coordinate guard, dialogue, affection, and deterministic story progress."""

    def __init__(self) -> None:
        max_concurrent = int(os.getenv("DIALOGUE_MAX_CONCURRENT", "5"))
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._input_guard = InputGuardAgent(self._semaphore)
        self._affection_judge = AffectionJudgeAgent(self._semaphore)
        print(f"AgentManager initialized; max concurrent agent calls: {max_concurrent}")

    @staticmethod
    def _empty_response(character: str) -> Dict[str, Any]:
        return {
            "messages": [{"speaker": character, "text": "（没有可用的输入）"}],
            "favorabilityChanges": AffectionJudgeAgent.normalize_changes({}),
            "favorabilityReasons": {},
            "inputGuard": {"allowed": True, "reasonCode": "OK", "systemMessage": ""},
            "storyProgress": {},
        }

    @staticmethod
    def _error_response(message: str) -> Dict[str, Any]:
        return {
            "messages": [{"speaker": "system", "text": message}],
            "favorabilityChanges": AffectionJudgeAgent.normalize_changes({}),
            "favorabilityReasons": {},
            "inputGuard": {"allowed": True, "reasonCode": "OK", "systemMessage": ""},
            "storyProgress": {},
        }

    async def generate_dialogue(
        self,
        character: str,
        conversation_history: list,
        story_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        try:
            last_role = conversation_history[-1].get("role") if conversation_history else ""
            last_message = (
                conversation_history[-1]["content"].strip()
                if conversation_history and "content" in conversation_history[-1]
                else ""
            )
            if not last_message:
                return self._empty_response(character)

            if last_role == "user":
                guard_result = await self._input_guard.check(last_message, story_context)
                if not guard_result["allowed"]:
                    return {
                        "messages": [{
                            "speaker": "system",
                            "text": guard_result["systemMessage"],
                        }],
                        "favorabilityChanges": AffectionJudgeAgent.normalize_changes({}),
                        "favorabilityReasons": {},
                        "inputGuard": guard_result,
                        "storyProgress": {},
                    }
            else:
                guard_result = {"allowed": True, "reasonCode": "OK", "systemMessage": ""}

            dialogue_agent = DialogueAgent(character, self._semaphore)
            responses = await dialogue_agent.generate(last_message, story_context)

            try:
                print("Agent responses:", json.dumps(responses, ensure_ascii=False))
            except Exception:
                pass

            affection_result = await self._affection_judge.judge(
                player_text=last_message,
                character=character,
                responses=responses,
                story_context=story_context,
            )
            favorability_changes = affection_result["favorabilityChanges"]
            story_progress = evaluate_story_progress(
                character,
                responses,
                story_context,
                favorability_changes,
            )

            return {
                "messages": responses,
                "favorabilityChanges": favorability_changes,
                "favorabilityReasons": affection_result["reasons"],
                "inputGuard": guard_result,
                "storyProgress": story_progress,
            }

        except Exception as exc:
            import traceback

            print(traceback.format_exc())
            return self._error_response(f"抱歉，调用AI时出现错误: {exc}")


agent_manager = AgentManager()


async def generate_dialogue(
    character: str,
    conversation_history: list,
    story_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compatibility wrapper used by main.py."""

    return await agent_manager.generate_dialogue(
        character,
        conversation_history,
        story_context,
    )
