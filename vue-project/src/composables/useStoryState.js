import { computed, ref } from 'vue';
import { storyNodes } from '../assets/storyNodes';

export function useStoryState(getCharacterName, options = {}) {
  const storyState = ref({
    currentNodeId: 'prologue',
    completedNodes: [],
    playerChoices: {},
    flags: {},
  });
  const nodeDialogueVisible = ref(false);
  const storyNotice = ref('');

  const currentNode = computed(() => storyNodes[storyState.value.currentNodeId]);
  const isFreeInteraction = computed(() => currentNode.value?.type === 'free_interaction');
  const storyPanelText = computed(() => {
    const node = currentNode.value;
    if (!node) return '';
    if (node.type === 'click_npc' && !nodeDialogueVisible.value) {
      return `请点击${getCharacterName(node.lockedCharacter)}听取暗示。`;
    }
    return node.text || '';
  });
  const canContinueStory = computed(() => {
    const node = currentNode.value;
    if (!node || isFreeInteraction.value || node.type === 'player_input') return false;
    if (node.type === 'click_npc') return Boolean(nodeDialogueVisible.value && node.nextNodes?.length);
    return Boolean(node.autoNext);
  });
  const dialoguePlaceholderText = computed(() => {
    const node = currentNode.value;
    if (!node) return '剧情加载中';
    if (node.type === 'free_interaction') return '点击NPC开始审问';
    if (node.type === 'click_npc') return `点击${getCharacterName(node.lockedCharacter)}推进剧情`;
    if (node.type === 'player_input') return '请选择你的回应';
    return '按剧情提示继续';
  });
  const storyContext = computed(() => {
    const node = currentNode.value;
    if (!node) return null;
    return {
      currentNodeId: node.nodeId,
      title: node.title,
      type: node.type,
      speaker: node.speaker,
      availableNextNodes: node.nextNodes || [],
      lockedCharacter: node.lockedCharacter,
      availableCharacters: node.availableCharacters || [],
      completedNodes: storyState.value.completedNodes,
      playerChoices: storyState.value.playerChoices,
    };
  });

  const pushSystemMessage = (content) => {
    storyNotice.value = content;
  };

  const advanceStory = (nextNodeId) => {
    if (!storyNodes[nextNodeId]) return;
    const currentId = storyState.value.currentNodeId;
    if (!storyState.value.completedNodes.includes(currentId)) {
      storyState.value.completedNodes.push(currentId);
    }
    storyState.value.currentNodeId = nextNodeId;
    storyNotice.value = '';
    nodeDialogueVisible.value = false;
    options.onStoryAdvanced?.();
  };

  const continueStory = () => {
    const node = currentNode.value;
    if (!node) return;
    if (node.type === 'click_npc' && node.nextNodes?.length) {
      advanceStory(node.nextNodes[0]);
      return;
    }
    if (node.autoNext) {
      advanceStory(node.autoNext);
    }
  };

  const chooseStoryOption = (choice) => {
    const node = currentNode.value;
    if (!node || node.type !== 'player_input') return;
    storyState.value.playerChoices[node.nodeId] = choice.id;
    options.onStoryChoice?.(choice);
    advanceStory(choice.nextNode);
  };

  const handleStoryCharacterClick = (characterId) => {
    const node = currentNode.value;
    if (!node) return { allowed: false, mode: 'blocked' };
    if (node.lockedCharacter && characterId !== node.lockedCharacter) {
      pushSystemMessage('此时不宜打断当前对话。');
      return { allowed: false, mode: 'blocked' };
    }
    if (node.availableCharacters?.length && !node.availableCharacters.includes(characterId)) {
      pushSystemMessage('现在还不是与此人交谈的时候。');
      return { allowed: false, mode: 'blocked' };
    }
    if (node.type === 'click_npc') {
      nodeDialogueVisible.value = true;
      storyNotice.value = '';
      return { allowed: true, mode: 'story_dialogue' };
    }
    if (!isFreeInteraction.value) {
      pushSystemMessage('当前剧情尚未进入自由审问阶段。');
      return { allowed: false, mode: 'blocked' };
    }
    return { allowed: true, mode: 'free_interaction' };
  };

  const applySuggestedNextNode = (suggestedNextNode) => {
    const node = currentNode.value;
    if (!node || !suggestedNextNode || suggestedNextNode === 'end') {
      return { applied: false, reason: 'NO_TRANSITION' };
    }
    const allowedNextNodes = node.nextNodes || [];
    if (!allowedNextNodes.includes(suggestedNextNode)) {
      pushSystemMessage(`系统已忽略非法剧情跳转：${suggestedNextNode}`);
      return { applied: false, reason: 'INVALID_TRANSITION' };
    }
    if (!storyNodes[suggestedNextNode]) {
      pushSystemMessage(`系统已忽略未配置剧情节点：${suggestedNextNode}`);
      return { applied: false, reason: 'UNKNOWN_NODE' };
    }
    advanceStory(suggestedNextNode);
    return { applied: true, reason: 'APPLIED' };
  };

  return {
    storyState,
    nodeDialogueVisible,
    storyNotice,
    currentNode,
    storyContext,
    isFreeInteraction,
    storyPanelText,
    canContinueStory,
    dialoguePlaceholderText,
    pushSystemMessage,
    advanceStory,
    continueStory,
    chooseStoryOption,
    handleStoryCharacterClick,
    applySuggestedNextNode,
  };
}
