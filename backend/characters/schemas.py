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
    "favorabilityChange是一个整数，范围只能是-5到5，由你根据玩家话语对当前NPC的影响程度判断。"
    "评分参考：严重冒犯、威胁或暴露破绽为-5到-3；轻微失礼或证据不足为-2到-1；普通试探或无明显影响为0；"
    "表达得体、有一定说服力为1到2；提供关键证据、击中当前NPC软肋或显著赢得信任为3到5。"
    "不要输出JSON以外的解释文本。"
    "例如：{'speaker': 'emperor', 'text': '...', 'nextNode': 'end', 'favorabilityChange': 3}"
)
