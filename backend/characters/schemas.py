"""Shared dialogue response schema instructions for character prompts."""

DIALOGUE_RESPONSE_FIELDS = (
    "speaker",
    "text",
)

DIALOGUE_RESPONSE_FORMAT = (
    "请以JSON格式返回，只包含'speaker'和'text'。"
    "speaker必须是当前NPC的角色ID。"
    "text是当前NPC展示给玩家的回复。"
    "你不能输出nextNode，不能决定剧情节点，不能更新证据或状态，不能输出好感度变化。"
    "剧情推进、证据更新和好感度变化由系统状态机与裁判Agent处理。"
    "不要输出JSON以外的解释文本。"
    '例如：{"speaker": "emperor", "text": "..."}'
)
