"""Rule-based story context retrieval for NPC prompts.

This module is intentionally not an LLM agent. It uses metadata filters,
keyword triggers, type quotas, leak rules, and compact context assembly to
keep each NPC prompt small and role-safe.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


STAGE_ORDER = {
    "stage_1": 1,
    "stage_2": 2,
    "stage_3": 3,
    "stage_4": 4,
    "stage_5": 5,
}

TYPE_QUOTAS = {
    "role_context": 2,
    "stage_rule": 1,
    "evidence_rule": 3,
    "npc_secret": 2,
    "world_rule": 1,
}

STORY_KNOWLEDGE = [
    {
        "id": "world_scene_qianqinggong",
        "type": "world_rule",
        "owners": ["emperor", "minister", "maid", "eunuch"],
        "stage_min": "stage_1",
        "keywords": ["乾清宫", "皇上", "审问", "血书", "朝堂"],
        "content": "今夜是乾清宫御前审问，四名NPC都在场，公开发言都会被其他人听见。",
    },
    {
        "id": "stage_free_interrogation",
        "type": "stage_rule",
        "owners": ["emperor", "minister", "maid", "eunuch"],
        "stage_min": "stage_2",
        "keywords": ["审问", "质问", "线索", "证据", "解释"],
        "content": "自由审问阶段中，NPC只能根据自身立场、已公开对话和自己知道的信息回应，不负责决定剧情节点。",
    },
    {
        "id": "stage_final_guard",
        "type": "stage_rule",
        "owners": ["emperor", "minister", "maid", "eunuch"],
        "stage_min": "stage_1",
        "keywords": ["最终", "裁断", "皇子", "拿问", "定罪"],
        "content": "未形成完整证据链前，任何NPC都不能直接把案件推进到最终裁断。",
    },
    {
        "id": "blood_letter_rule",
        "type": "evidence_rule",
        "owners": ["emperor", "minister", "maid", "eunuch"],
        "stage_min": "stage_1",
        "keywords": ["血书", "密信", "谋逆", "皇子", "边将"],
        "content": "血书密信是真实线索，但单独只能指向谋逆风险，不能单独定罪皇子或张廷玉。",
    },
    {
        "id": "handwriting_evidence_rule",
        "type": "evidence_rule",
        "owners": ["maid", "emperor"],
        "public_after_evidence": "handwritingHint",
        "stage_min": "stage_2",
        "keywords": ["笔迹", "纸料", "血书", "内侍", "旧人"],
        "content": "血书笔迹线索指向旧日宫中一名被调往江南的内侍，可补强血书不是普通伪造。",
    },
    {
        "id": "entry_record_rule",
        "type": "evidence_rule",
        "owners": ["eunuch", "emperor"],
        "public_after_evidence": "palaceEntryRecord",
        "stage_min": "stage_2",
        "keywords": ["入宫", "出入", "乾清宫外", "见过谁", "偏门", "门人"],
        "content": "乾清宫出入记录可证明张廷玉入宫前见过皇子府门人，密信在玩家入宫前可能被动过。",
    },
    {
        "id": "ledger_evidence_rule",
        "type": "evidence_rule",
        "owners": ["minister", "emperor"],
        "public_after_evidence": "ledgerClue",
        "stage_min": "stage_2",
        "keywords": ["户部", "银两", "副账", "账册", "粮草"],
        "content": "户部副账线索连接江南科场舞弊、银两流向和边军粮草，是证据链的重要部分。",
    },
    {
        "id": "border_army_rule",
        "type": "evidence_rule",
        "owners": ["minister", "emperor"],
        "public_after_evidence": "borderArmyLink",
        "stage_min": "stage_4",
        "keywords": ["边军", "粮草", "边疆", "大将", "军中"],
        "content": "边军粮草线索连接皇子、江南银两和边疆大将，是进入最终判断前的核心线索。",
    },
    {
        "id": "emperor_role",
        "type": "role_context",
        "owners": ["emperor"],
        "stage_min": "stage_1",
        "keywords": ["皇上", "玄烨", "裁断", "国本", "证据"],
        "content": "玄烨重视皇权、朝局稳定和证据链。他会施压，但不会替玩家补全证据链。",
    },
    {
        "id": "minister_role",
        "type": "role_context",
        "owners": ["minister"],
        "stage_min": "stage_1",
        "keywords": ["张廷玉", "大臣", "朝局", "国本", "弹劾"],
        "content": "张廷玉表面维护国本与朝纲，实则压下关键证据以避免朝局失控；面对铁证时会强调大局。",
    },
    {
        "id": "maid_role",
        "type": "role_context",
        "owners": ["maid"],
        "stage_min": "stage_1",
        "keywords": ["苏麻喇姑", "姑姑", "笔迹", "礼法", "分寸"],
        "content": "苏麻喇姑熟悉宫廷旧事，重视克制、礼法和皇帝心理底线；她只会谨慎提醒，不替玩家直接定罪。",
    },
    {
        "id": "eunuch_role",
        "type": "role_context",
        "owners": ["eunuch"],
        "stage_min": "stage_1",
        "keywords": ["李德全", "公公", "奴才", "出入", "乾清宫"],
        "content": "李德全掌握宫中出入消息，但怕卷入党争；玩家问法谨慎时，他才会给旁证。",
    },
    {
        "id": "minister_hidden_ledger",
        "type": "npc_secret",
        "owners": ["minister"],
        "stage_min": "stage_2",
        "keywords": ["户部", "副账", "压下", "银两", "粮草"],
        "content": "张廷玉知道自己曾压下一份户部副账，也知道江南银两与边军粮草有关。",
    },
    {
        "id": "maid_hidden_handwriting",
        "type": "npc_secret",
        "owners": ["maid"],
        "stage_min": "stage_2",
        "keywords": ["笔迹", "血书", "纸料", "内侍", "旧人"],
        "content": "苏麻喇姑知道血书笔迹与旧日宫中一名被调往江南的内侍有关。",
    },
    {
        "id": "eunuch_hidden_entry",
        "type": "npc_secret",
        "owners": ["eunuch"],
        "stage_min": "stage_2",
        "keywords": ["入宫", "见过谁", "偏门", "门人", "动过"],
        "content": "李德全知道张廷玉入宫前见过皇子府门人，也知道御案上的血书可能被人动过。",
    },
]


def _stage_rank(stage_id: str | None) -> int:
    return STAGE_ORDER.get(stage_id or "stage_1", 1)


def _truthy_evidence(story_context: Dict[str, Any]) -> Dict[str, bool]:
    scene_memory = story_context.get("sceneMemory") or {}
    evidence = scene_memory.get("evidence") or {}
    return evidence if isinstance(evidence, dict) else {}


def _truthy_flags(story_context: Dict[str, Any]) -> Dict[str, bool]:
    scene_memory = story_context.get("sceneMemory") or {}
    flags = scene_memory.get("flags") or {}
    return flags if isinstance(flags, dict) else {}


def _recent_turns(story_context: Dict[str, Any], limit: int = 8) -> List[Dict[str, str]]:
    scene_memory = story_context.get("sceneMemory") or {}
    turns = scene_memory.get("recentTurns") or []
    if not isinstance(turns, list):
        return []
    compact_turns = []
    for item in turns[-limit:]:
        if not isinstance(item, dict):
            continue
        speaker = item.get("speaker")
        text = item.get("text")
        if isinstance(speaker, str) and isinstance(text, str) and text.strip():
            compact_turns.append({"speaker": speaker, "text": text.strip()})
    return compact_turns


def _metadata_allowed(
    item: Dict[str, Any],
    character: str,
    stage_id: str | None,
    evidence: Dict[str, bool],
    flags: Dict[str, bool],
) -> bool:
    owners = item.get("owners") or []
    if character not in owners:
        public_after_evidence = item.get("public_after_evidence")
        public_after_flag = item.get("public_after_flag")
        if public_after_evidence and evidence.get(public_after_evidence):
            pass
        elif public_after_flag and flags.get(public_after_flag):
            pass
        else:
            return False

    if _stage_rank(stage_id) < _stage_rank(item.get("stage_min")):
        return False

    required_evidence = item.get("requires_evidence") or []
    if any(not evidence.get(evidence_id) for evidence_id in required_evidence):
        return False

    required_flags = item.get("requires_flags") or []
    if any(not flags.get(flag_id) for flag_id in required_flags):
        return False

    return True


def _keyword_score(item: Dict[str, Any], trigger_text: str) -> int:
    text = trigger_text.lower()
    score = 0
    for keyword in item.get("keywords") or []:
        if keyword.lower() in text:
            score += 3
    if item.get("type") in {"role_context", "world_rule"}:
        score += 1
    return score


def _select_with_type_quotas(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected = []
    used_by_type: Dict[str, int] = defaultdict(int)
    for item in sorted(items, key=lambda chunk: (-chunk["score"], chunk["id"])):
        item_type = item.get("type") or "misc"
        quota = TYPE_QUOTAS.get(item_type, 1)
        if used_by_type[item_type] >= quota:
            continue
        selected.append(item)
        used_by_type[item_type] += 1
    return selected[:8]


def build_dynamic_state(
    character: str,
    trigger_text: str,
    story_context: Dict[str, Any] | None,
) -> Dict[str, Any]:
    story_context = story_context or {}
    current_stage = story_context.get("currentStage") or {}
    scene_memory = story_context.get("sceneMemory") or {}
    return {
        "currentNodeId": story_context.get("currentNodeId"),
        "nodeTitle": story_context.get("title"),
        "nodeType": story_context.get("type"),
        "currentStageId": story_context.get("currentStageId"),
        "currentStageName": current_stage.get("name") if isinstance(current_stage, dict) else None,
        "currentStageGoal": current_stage.get("goal") if isinstance(current_stage, dict) else None,
        "targetCharacter": character,
        "speakingOrder": story_context.get("speakingOrder") or [],
        "completedNodes": story_context.get("completedNodes") or [],
        "evidence": _truthy_evidence(story_context),
        "flags": _truthy_flags(story_context),
        "recentTurns": _recent_turns(story_context),
        "interrogationState": story_context.get("interrogationState") or {},
        "triggerText": trigger_text,
        "sceneSummary": scene_memory.get("summary") if isinstance(scene_memory, dict) else "",
    }


def retrieve_story_context(
    character: str,
    trigger_text: str,
    story_context: Dict[str, Any] | None,
) -> Dict[str, Any]:
    story_context = story_context or {}
    stage_id = story_context.get("currentStageId") or "stage_1"
    evidence = _truthy_evidence(story_context)
    flags = _truthy_flags(story_context)

    candidates = []
    for item in STORY_KNOWLEDGE:
        if not _metadata_allowed(item, character, stage_id, evidence, flags):
            continue
        score = _keyword_score(item, trigger_text)
        if score <= 0:
            continue
        candidates.append({**item, "score": score})

    selected = _select_with_type_quotas(candidates)
    return {
        "dynamicState": build_dynamic_state(character, trigger_text, story_context),
        "retrievedContext": [
            {
                "id": item["id"],
                "type": item["type"],
                "content": item["content"],
            }
            for item in selected
        ],
        "retrievalPolicy": {
            "metadataFilter": "owner/stage/evidence/flag",
            "keywordTrigger": True,
            "typeQuotas": TYPE_QUOTAS,
            "antiLeak": "hidden chunks are only visible to owner unless already public",
            "minimalContext": True,
        },
    }
