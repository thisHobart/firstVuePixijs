"""Affection and attitude judge agent."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from story.retriever import retrieve_story_context

from .base import BaseAgent, extract_json_from_text


SYSTEM_MESSAGE = (
    "你是《宫廷风云》的好感度裁判Agent。"
    "你不生成剧情台词，只根据本轮玩家发言、NPC回复、案件状态和四名NPC目标/恐惧，"
    "判断 emperor、minister、maid、eunuch 四人的好感度变化。"
    "你必须分别判断四名NPC的利益、恐惧和立场变化，不能简单让所有角色同涨同跌。"
    "同一句话可能让一方上升、另一方下降，也可能让某个角色不变。"
    "变化范围为-10到10：0表示无明显影响；1到3表示轻微倾向；4到6表示明显影响；"
    "7到10表示关键立场变化、重大突破、严重冒犯或直接威胁。"
    "评分必须考虑同场景公开影响：四名NPC都在乾清宫内，都会听见公开对话。"
    "皇帝、苏麻喇姑、李德全通常更看重证据链、克制、皇权稳定和查明真相；"
    "张廷玉是压案阻力方，玩家替他缓颊、弱化血书或放弃追查时，他可能上升；"
    "玩家抓住户部副账、皇子府门人、边军粮草、压证矛盾时，他通常下降。"
    "输出必须是JSON，不要输出解释文本。格式："
    '{"favorabilityChanges":{"emperor":0,"minister":0,"maid":0,"eunuch":0},'
    '"reasons":{"emperor":"...","minister":"...","maid":"...","eunuch":"..."}}'
)


class AffectionJudgeAgent(BaseAgent):
    """Judge per-NPC favorability deltas after a visible dialogue turn."""

    def __init__(self, semaphore: asyncio.Semaphore) -> None:
        super().__init__(
            name="affection_judge",
            system_message=SYSTEM_MESSAGE,
            semaphore=semaphore,
            timeout_seconds=120,
            max_attempts=3,
        )

    @staticmethod
    def normalize_changes(value: Any) -> Dict[str, int]:
        changes = value if isinstance(value, dict) else {}
        normalized: Dict[str, int] = {}
        for character in ("emperor", "minister", "maid", "eunuch"):
            try:
                delta = int(changes.get(character, 0))
            except (TypeError, ValueError):
                delta = 0
            normalized[character] = max(-10, min(10, delta))
        return normalized

    @staticmethod
    def build_task(
        player_text: str,
        character: str,
        responses: List[Dict[str, Any]],
        story_context: Dict[str, Any] | None,
    ) -> str:
        story_context = story_context or {}
        retrieved_context = retrieve_story_context(character, player_text, story_context)
        return (
            "请评估本轮公开对话对四名NPC好感度的影响。\n"
            f"玩家本轮发言：{player_text}\n"
            f"当前被审问对象：{character}\n"
            f"本轮NPC回复：{json.dumps(responses, ensure_ascii=False)}\n"
            f"剧情上下文：{json.dumps(retrieved_context, ensure_ascii=False)}\n"
            "评分范围：每个角色-10到10。0表示无明显影响；1到3轻微；4到6明显；7到10关键或严重。"
            "必须独立评估每个NPC，禁止因为玩家说得“好/坏”就让所有角色同向变化。"
            "判断方向："
            "1. 玩家冷静推进证据链、尊重证据、维护皇权稳定，通常使emperor/maid/eunuch上升，minister下降。"
            "2. 玩家替张廷玉缓颊、承认证据不足、弱化血书价值、放弃追问户部副账/皇子府门人，通常使minister上升，emperor/maid可能下降。"
            "3. 玩家无证据直接指控皇子或逼皇帝表态，emperor/maid通常下降；minister可能上升，因为他获得攻击玩家失礼和证据不足的理由。"
            "4. 玩家威胁李德全或逼其直接指认皇子，eunuch下降；即使这句话有利于查案，也不能简单给eunuch加分。"
            "5. 玩家抓住张廷玉压证、户部副账、皇子府门人、边军粮草等软肋，minister下降，emperor可能上升。"
            "6. 如果玩家行为同时有利有弊，可以给不同角色不同幅度，或对单个角色给较小变化。"
        )

    async def judge(
        self,
        player_text: str,
        character: str,
        responses: List[Dict[str, Any]],
        story_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        raw_text = await self.run_text(
            self.build_task(player_text, character, responses, story_context),
            '{"favorabilityChanges":{"emperor":0,"minister":0,"maid":0,"eunuch":0},"reasons":{}}',
        )
        try:
            data = extract_json_from_text(raw_text)
        except json.JSONDecodeError:
            data = {}
        if not isinstance(data, dict):
            data = {}

        return {
            "favorabilityChanges": self.normalize_changes(data.get("favorabilityChanges")),
            "reasons": data.get("reasons") if isinstance(data.get("reasons"), dict) else {},
        }
