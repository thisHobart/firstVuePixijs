import { computed, ref } from 'vue';
import { storyNodes } from '../assets/storyNodes';

export function useStoryState(getCharacterName, options = {}) {
  const storyState = ref({
    currentNodeId: 'prologue',
    completedNodes: [],
    playerChoices: {},
    flags: {},
  });
  const sceneMemory = ref({
    summary: '玩家正在乾清宫内证明血书密信真伪，并试图在半个时辰内找出皇子党与边将勾结的证据。',
    recentTurns: [],
    evidence: ['blood_letter'],
    flags: {
      ministerContradiction: false,
      maidHint: false,
      eunuchWitness: false,
      emperorTrust: false,
    },
  });
  const npcMemory = ref({
    emperor: {
      stance: 'test_everyone',
      notes: ['表面震怒，实则观察殿内众人的反应。'],
      lastClaims: [],
    },
    minister: {
      stance: 'protect_prince',
      notes: ['表面维护国本，实则暗中袒护涉案皇子。'],
      lastClaims: [],
    },
    maid: {
      stance: 'protect_emperor',
      notes: ['知道皇帝真正的心理底线，但不能直接明说。'],
      lastClaims: [],
    },
    eunuch: {
      stance: 'self_preservation',
      notes: ['知道今夜乾清宫内外出入记录，但怕牵连自身。'],
      lastClaims: [],
    },
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
  const getStoryContext = (targetCharacter, speakingOrder = []) => {
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
      targetCharacter,
      speakingOrder,
      sceneMemory: sceneMemory.value,
      npcMemory: npcMemory.value,
    };
  };

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

  const appendSceneTurn = (speaker, text) => {
    if (!speaker || !text) return;
    sceneMemory.value.recentTurns.push({ speaker, text });
    sceneMemory.value.recentTurns = sceneMemory.value.recentTurns.slice(-12);
  };

  const chooseStoryOption = (choice) => {
    const node = currentNode.value;
    if (!node || node.type !== 'player_input') return;
    storyState.value.playerChoices[node.nodeId] = choice.id;
    appendSceneTurn('player', choice.text);
    options.onStoryChoice?.(choice);
    advanceStory(choice.nextNode);
  };

  const decideSpeakingOrder = (targetCharacter) => {
    if (!isFreeInteraction.value) return [targetCharacter];
    const flags = sceneMemory.value.flags;
    if (targetCharacter === 'minister') {
      return flags.eunuchWitness
        ? ['minister', 'maid', 'emperor']
        : ['minister'];
    }
    if (targetCharacter === 'maid') {
      return ['maid', 'emperor'];
    }
    if (targetCharacter === 'eunuch') {
      return ['eunuch', 'minister'];
    }
    if (targetCharacter === 'emperor') {
      return ['emperor', 'minister'];
    }
    return [targetCharacter];
  };

  const applyAgentResult = (speaker, message) => {
    appendSceneTurn(message.role || speaker, message.content);

    const allowedFlagBySpeaker = {
      minister: 'ministerContradiction',
      maid: 'maidHint',
      eunuch: 'eunuchWitness',
      emperor: 'emperorTrust',
    };
    const allowedFlag = allowedFlagBySpeaker[speaker];
    const stateUpdates = message.stateUpdates || {};
    if (allowedFlag && typeof stateUpdates[allowedFlag] === 'boolean') {
      sceneMemory.value.flags[allowedFlag] = stateUpdates[allowedFlag];
    }

    const evidenceUpdates = Array.isArray(message.evidenceUpdates)
      ? message.evidenceUpdates
      : [];
    for (const evidence of evidenceUpdates) {
      if (typeof evidence === 'string' && !sceneMemory.value.evidence.includes(evidence)) {
        sceneMemory.value.evidence.push(evidence);
      }
    }

    if (npcMemory.value[speaker]) {
      npcMemory.value[speaker].lastClaims.push(message.content);
      npcMemory.value[speaker].lastClaims = npcMemory.value[speaker].lastClaims.slice(-4);
    }
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
    sceneMemory,
    npcMemory,
    nodeDialogueVisible,
    storyNotice,
    currentNode,
    getStoryContext,
    isFreeInteraction,
    storyPanelText,
    canContinueStory,
    dialoguePlaceholderText,
    pushSystemMessage,
    advanceStory,
    continueStory,
    chooseStoryOption,
    appendSceneTurn,
    decideSpeakingOrder,
    applyAgentResult,
    handleStoryCharacterClick,
    applySuggestedNextNode,
  };
}
