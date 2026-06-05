"""Deterministic story progress evaluation.

NPC agents only generate dialogue. This module owns evidence detection,
stage transitions, and pending story node selection.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


STAGE_ORDER = {
    "stage_1": 1,
    "stage_2": 2,
    "stage_3": 3,
    "stage_4": 4,
    "stage_5": 5,
}

EVIDENCE_IDS = {
    "bloodLetter",
    "handwritingHint",
    "palaceEntryRecord",
    "ledgerClue",
    "borderArmyLink",
}

FLAG_IDS = {
    "ministerContradictionFound",
    "ministerLedgerSuppressed",
    "maidHandwritingHint",
    "eunuchEntryRecord",
    "emperorTrust",
    "finalJudgementReady",
}

NEXT_NODES = [
    "final_judgement",
    "evidence_chain_forming",
    "minister_breakthrough",
    "maid_testimony",
    "eunuch_secret",
]


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    normalized = str(text or "").lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def _get_evidence(story_context: Dict[str, Any]) -> Dict[str, bool]:
    scene_memory = story_context.get("sceneMemory") or {}
    evidence = scene_memory.get("evidence") or {}
    return {
        evidence_id: bool(evidence.get(evidence_id))
        for evidence_id in EVIDENCE_IDS
    }


def _get_flags(story_context: Dict[str, Any]) -> Dict[str, bool]:
    scene_memory = story_context.get("sceneMemory") or {}
    flags = scene_memory.get("flags") or {}
    return {
        flag_id: bool(flags.get(flag_id))
        for flag_id in FLAG_IDS
    }


def _get_favorability(story_context: Dict[str, Any], deltas: Dict[str, int]) -> Dict[str, int]:
    snapshot = story_context.get("favorabilitySnapshot") or {}
    values: Dict[str, int] = {}
    for character in ("emperor", "minister", "maid", "eunuch"):
        try:
            base = int(snapshot.get(character, 50))
        except (TypeError, ValueError):
            base = 50
        try:
            delta = int(deltas.get(character, 0))
        except (TypeError, ValueError):
            delta = 0
        values[character] = base + delta
    return values


def _visited_count(story_context: Dict[str, Any]) -> int:
    interrogation = story_context.get("interrogationState") or {}
    visited = interrogation.get("visitedCharacters") or []
    return len(visited) if isinstance(visited, list) else 0


def _stage_from_state(
    current_node_id: str,
    evidence: Dict[str, bool],
    flags: Dict[str, bool],
    favorability: Dict[str, int],
    visited_count: int,
) -> str:
    has_core_evidence_chain = (
        evidence["bloodLetter"]
        and evidence["handwritingHint"]
        and evidence["palaceEntryRecord"]
        and evidence["ledgerClue"]
        and evidence["borderArmyLink"]
    )
    has_support_from_allies = (
        favorability["emperor"] >= 60
        and (favorability["maid"] >= 55 or evidence["handwritingHint"])
        and (favorability["eunuch"] >= 60 or evidence["palaceEntryRecord"])
    )
    has_villain_exposed = (
        flags["ministerContradictionFound"]
        and favorability["minister"] <= 35
    )
    has_court_confrontation = visited_count >= 3

    if has_support_from_allies and has_villain_exposed and has_core_evidence_chain and has_court_confrontation:
        return "stage_5"
    if evidence["ledgerClue"] and evidence["palaceEntryRecord"] and flags["ministerContradictionFound"]:
        return "stage_4"
    if evidence["handwritingHint"] or evidence["palaceEntryRecord"] or flags["ministerContradictionFound"]:
        return "stage_3"
    if current_node_id == "free_interrogation" or visited_count > 0:
        return "stage_2"
    return "stage_1"


def _mark(mapping: Dict[str, bool], key: str, updates: List[str]) -> None:
    if key in mapping and not mapping[key]:
        mapping[key] = True
        updates.append(key)


def _detect_from_dialogue(
    speaker: str,
    text: str,
    stage_id: str,
    evidence: Dict[str, bool],
    flags: Dict[str, bool],
    favorability: Dict[str, int],
    evidence_updates: List[str],
    flag_updates: Dict[str, bool],
) -> None:
    local_flag_updates: List[str] = []

    if (
        speaker == "maid"
        and favorability["maid"] >= 60
        and _contains_any(text, ["笔迹", "纸料", "旧日", "内侍", "江南的内侍", "不像临时伪造"])
    ):
        _mark(flags, "maidHandwritingHint", local_flag_updates)
        _mark(evidence, "handwritingHint", evidence_updates)

    if (
        speaker == "eunuch"
        and favorability["eunuch"] >= 60
        and _contains_any(text, ["入宫", "乾清宫外", "偏门", "门人", "出入", "动过", "血书被"])
    ):
        _mark(flags, "eunuchEntryRecord", local_flag_updates)
        _mark(evidence, "palaceEntryRecord", evidence_updates)

    if (
        speaker == "minister"
        and favorability["minister"] <= 40
        and _contains_any(text, ["户部", "副账", "账册", "银两", "压下", "粮草"])
    ):
        _mark(flags, "ministerLedgerSuppressed", local_flag_updates)
        _mark(evidence, "ledgerClue", evidence_updates)

    if (
        speaker == "minister"
        and favorability["minister"] <= 45
        and _contains_any(text, ["臣为大局", "大局", "老臣确曾", "确曾", "压下"])
    ):
        _mark(flags, "ministerContradictionFound", local_flag_updates)

    if (
        speaker in {"minister", "emperor"}
        and (
            stage_id == "stage_4"
            or (
                evidence["ledgerClue"]
                and evidence["palaceEntryRecord"]
                and flags["ministerContradictionFound"]
            )
        )
        and favorability["minister"] <= 35
        and favorability["emperor"] >= 60
        and evidence["ledgerClue"]
        and evidence["palaceEntryRecord"]
        and flags["ministerContradictionFound"]
        and _contains_any(text, ["边军", "边疆", "北疆", "边镇", "粮草", "粮饷", "粮道", "粮道折报", "军需", "军饷", "大将", "军中"])
    ):
        _mark(evidence, "borderArmyLink", evidence_updates)

    for flag_id in local_flag_updates:
        flag_updates[flag_id] = True


def _select_pending_node(
    current_node_id: str,
    completed_nodes: List[str],
    evidence: Dict[str, bool],
    flags: Dict[str, bool],
) -> str | None:
    if current_node_id != "free_interrogation":
        return None
    completed = set(completed_nodes if isinstance(completed_nodes, list) else [])

    def available(node_id: str) -> bool:
        return node_id in NEXT_NODES and node_id not in completed

    if flags["finalJudgementReady"] and available("final_judgement"):
        return "final_judgement"
    if (
        (evidence["handwritingHint"] or evidence["palaceEntryRecord"] or evidence["ledgerClue"])
        and available("evidence_chain_forming")
    ):
        return "evidence_chain_forming"
    if (
        (flags["ministerContradictionFound"] or flags["ministerLedgerSuppressed"])
        and available("minister_breakthrough")
    ):
        return "minister_breakthrough"
    if evidence["handwritingHint"] and available("maid_testimony"):
        return "maid_testimony"
    if evidence["palaceEntryRecord"] and available("eunuch_secret"):
        return "eunuch_secret"
    return None


def evaluate_story_progress(
    character: str,
    responses: List[Dict[str, Any]],
    story_context: Dict[str, Any] | None,
    favorability_changes: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    story_context = story_context or {}
    current_node_id = story_context.get("currentNodeId") or ""
    current_stage_id = story_context.get("currentStageId") or "stage_1"
    completed_nodes = story_context.get("completedNodes") or []

    evidence = _get_evidence(story_context)
    flags = _get_flags(story_context)
    favorability = _get_favorability(story_context, favorability_changes or {})
    visited = _visited_count(story_context)

    evidence_updates: List[str] = []
    flag_updates: Dict[str, bool] = {}

    for response in responses:
        if not isinstance(response, dict):
            continue
        speaker = response.get("speaker")
        text = response.get("text")
        if not isinstance(speaker, str):
            speaker = character
        if not isinstance(text, str):
            continue
        _detect_from_dialogue(
            speaker,
            text,
            current_stage_id,
            evidence,
            flags,
            favorability,
            evidence_updates,
            flag_updates,
        )

    next_stage_id = _stage_from_state(current_node_id, evidence, flags, favorability, visited)
    flags["finalJudgementReady"] = next_stage_id == "stage_5"
    flag_updates["finalJudgementReady"] = flags["finalJudgementReady"]

    pending_node = _select_pending_node(current_node_id, completed_nodes, evidence, flags)
    notice = ""
    if pending_node:
        notice = "剧情状态已满足新的推进条件，请先阅读当前对话，再点击“继续”。"

    return {
        "evidenceUpdates": evidence_updates,
        "flagUpdates": flag_updates,
        "currentStageId": next_stage_id,
        "pendingStoryNode": pending_node,
        "notice": notice,
    }
