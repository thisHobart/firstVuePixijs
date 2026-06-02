"""Shared dialogue response schema instructions for character prompts."""

DIALOGUE_RESPONSE_FIELDS = (
    "speaker",
    "text",
    "nextNode",
    "favorabilityChange",
)

DIALOGUE_RESPONSE_FORMAT = (
    "请以JSON格式返回，包含'speaker', 'text', 'nextNode'和'favorabilityChange'。"
    "speaker必须是当前NPC的角色ID。"
    "text是当前NPC展示给玩家的回复。"
    "nextNode表示下一剧情节点；如果剧情不推进，返回'end'。"
    "favorabilityChange是一个整数，只能是-1（好感度下降）、0（不变）或1（好感度上升）。"
    "不要输出JSON以外的解释文本。"
    "例如：{'speaker': 'emperor', 'text': '...', 'nextNode': 'end', 'favorabilityChange': 1}"
)
