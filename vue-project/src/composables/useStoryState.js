import { computed, ref } from 'vue';
import {
  caseTruth,
  createInitialEvidenceState,
  createInitialInterrogationState,
  evidenceChain,
  interruptionRules,
  npcProfiles,
  storyStages,
} from '../assets/caseDesign';
import { storyNodes } from '../assets/storyNodes';

const evidenceAliases = {
  blood_letter: 'bloodLetter',
  maidHint: 'handwritingHint',
  eunuchWitness: 'palaceEntryRecord',
  ministerContradiction: 'ledgerClue',
};

const flagAliases = {
  ministerContradiction: 'ministerContradictionFound',
  maidHint: 'maidHandwritingHint',
  eunuchWitness: 'eunuchEntryRecord',
};

export function useStoryState(getCharacterName, options = {}) {
  const storyState = ref({
    currentNodeId: 'prologue',
    currentStageId: 'stage_1',
    completedNodes: [],
    playerChoices: {},
    interrogation: createInitialInterrogationState(),
    flags: {
      ministerContradictionFound: false,
      ministerLedgerSuppressed: false,
      recklessAccusation: false,
      finalJudgementReady: false,
    },
  });
  const sceneMemory = ref({
    summary: caseTruth.summary,
    recentTurns: [],
    evidence: createInitialEvidenceState(),
    flags: {
      ministerContradictionFound: false,
      ministerLedgerSuppressed: false,
      maidHandwritingHint: false,
      eunuchEntryRecord: false,
      emperorTrust: false,
      finalJudgementReady: false,
    },
  });
  const npcMemory = ref({
    emperor: {
      stance: 'test_everyone',
      goal: npcProfiles.emperor.goal,
      fear: npcProfiles.emperor.fear,
      knows: npcProfiles.emperor.knows,
      hides: npcProfiles.emperor.hides,
      notes: ['表面震怒，实则观察殿内众人的反应。'],
      lastClaims: [],
    },
    minister: {
      stance: 'protect_prince',
      goal: npcProfiles.minister.goal,
      fear: npcProfiles.minister.fear,
      knows: npcProfiles.minister.knows,
      hides: npcProfiles.minister.hides,
      notes: ['表面维护国本，实则压下关键证据以保住朝局。'],
      lastClaims: [],
    },
    maid: {
      stance: 'protect_emperor',
      goal: npcProfiles.maid.goal,
      fear: npcProfiles.maid.fear,
      knows: npcProfiles.maid.knows,
      hides: npcProfiles.maid.hides,
      notes: ['知道皇帝真正的心理底线，但不能直接明说。'],
      lastClaims: [],
    },
    eunuch: {
      stance: 'self_preservation',
      goal: npcProfiles.eunuch.goal,
      fear: npcProfiles.eunuch.fear,
      knows: npcProfiles.eunuch.knows,
      hides: npcProfiles.eunuch.hides,
      notes: ['知道今夜乾清宫内外出入记录，但怕牵连自身。'],
      lastClaims: [],
    },
  });
  const nodeDialogueVisible = ref(false);
  const storyNotice = ref('');
  const pendingSuggestedNextNode = ref(null);

  const currentNode = computed(() => storyNodes[storyState.value.currentNodeId]);
  const currentStage = computed(() => storyStages[storyState.value.currentStageId]);
  const isFreeInteraction = computed(() => currentNode.value?.type === 'free_interaction');
  const normalizeEvidenceId = (evidenceId) => evidenceAliases[evidenceId] || evidenceId;
  const normalizeFlagId = (flagId) => flagAliases[flagId] || flagId;
  const hasEvidence = (evidenceId) => Boolean(sceneMemory.value.evidence[normalizeEvidenceId(evidenceId)]);
  const markEvidence = (evidenceId) => {
    evidenceId = normalizeEvidenceId(evidenceId);
    if (!Object.prototype.hasOwnProperty.call(evidenceChain, evidenceId)) return false;
    if (sceneMemory.value.evidence[evidenceId]) return false;
    sceneMemory.value.evidence[evidenceId] = true;
    return true;
  };
  const markFlag = (flagId, value = true) => {
    flagId = normalizeFlagId(flagId);
    if (!Object.prototype.hasOwnProperty.call(sceneMemory.value.flags, flagId)) return false;
    sceneMemory.value.flags[flagId] = value;
    if (Object.prototype.hasOwnProperty.call(storyState.value.flags, flagId)) {
      storyState.value.flags[flagId] = value;
    }
    return true;
  };
  const updateStoryStage = () => {
    const visitedCount = storyState.value.interrogation.visitedCharacters.length;
    const flags = sceneMemory.value.flags;
    if (
      hasEvidence('borderArmyLink') ||
      (hasEvidence('handwritingHint') &&
        hasEvidence('palaceEntryRecord') &&
        hasEvidence('ledgerClue') &&
        flags.ministerContradictionFound)
    ) {
      storyState.value.currentStageId = 'stage_5';
      markFlag('finalJudgementReady', true);
      return;
    }
    if (hasEvidence('ledgerClue') && hasEvidence('palaceEntryRecord') && flags.ministerContradictionFound) {
      storyState.value.currentStageId = 'stage_4';
      return;
    }
    if (hasEvidence('handwritingHint') || hasEvidence('palaceEntryRecord') || flags.ministerContradictionFound) {
      storyState.value.currentStageId = 'stage_3';
      return;
    }
    if (isFreeInteraction.value || visitedCount > 0) {
      storyState.value.currentStageId = 'stage_2';
      return;
    }
    storyState.value.currentStageId = 'stage_1';
  };
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
    if (pendingSuggestedNextNode.value) return true;
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
      currentStageId: storyState.value.currentStageId,
      currentStage: currentStage.value,
      caseTruth,
      evidenceChain,
      npcProfiles,
      interruptionRules,
      interrogationState: storyState.value.interrogation,
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
    pendingSuggestedNextNode.value = null;
    const currentId = storyState.value.currentNodeId;
    if (!storyState.value.completedNodes.includes(currentId)) {
      storyState.value.completedNodes.push(currentId);
    }
    storyState.value.currentNodeId = nextNodeId;
    storyNotice.value = '';
    nodeDialogueVisible.value = false;
    updateStoryStage();
    options.onStoryAdvanced?.();
  };

  const continueStory = () => {
    if (pendingSuggestedNextNode.value) {
      advanceStory(pendingSuggestedNextNode.value);
      return;
    }
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
    sceneMemory.value.recentTurns = sceneMemory.value.recentTurns.slice(-18);
  };

  const chooseStoryOption = (choice) => {
    const node = currentNode.value;
    if (!node || node.type !== 'player_input') return;
    storyState.value.playerChoices[node.nodeId] = choice.id;
    appendSceneTurn('player', choice.text);
    options.onStoryChoice?.(choice);
    advanceStory(choice.nextNode);
  };

  const recordInterrogationTurn = (targetCharacter) => {
    const interrogation = storyState.value.interrogation;
    interrogation.currentTarget = targetCharacter;
    if (Object.prototype.hasOwnProperty.call(interrogation.turnCounts, targetCharacter)) {
      interrogation.turnCounts[targetCharacter] += 1;
    }
    if (!interrogation.visitedCharacters.includes(targetCharacter)) {
      interrogation.visitedCharacters.push(targetCharacter);
    }
    updateStoryStage();
  };

  const addInterjection = (order, speaker, ruleId, once = true) => {
    const interrogation = storyState.value.interrogation;
    if (!speaker || order.includes(speaker)) return;
    if (once && interrogation.triggeredInterjections.includes(ruleId)) return;
    order.push(speaker);
    if (ruleId) {
      interrogation.triggeredInterjections.push(ruleId);
    }
  };

  const decideSpeakingOrder = (targetCharacter) => {
    if (!isFreeInteraction.value) return [targetCharacter];
    recordInterrogationTurn(targetCharacter);
    const flags = sceneMemory.value.flags;
    const getFavorability =
      typeof options.getCharacterFavorability === 'function'
        ? options.getCharacterFavorability
        : () => 50;
    const order = [targetCharacter];
    const turns = storyState.value.interrogation.turnCounts;

    if (targetCharacter === 'minister') {
      const ministerTurns = turns.minister || 0;
      const ministerFavorability = getFavorability('minister');

      if (ministerTurns >= 1 || ministerFavorability <= 45 || flags.ministerContradictionFound) {
        addInterjection(order, 'emperor', 'minister_emperor_pressure');
      }
      if (
        ministerTurns >= 2 ||
        ministerFavorability <= 40 ||
        hasEvidence('handwritingHint') ||
        flags.ministerContradictionFound
      ) {
        addInterjection(order, 'maid', 'minister_maid_handwriting');
      }
      if (hasEvidence('palaceEntryRecord') || ministerFavorability <= 35 || flags.eunuchEntryRecord) {
        addInterjection(order, 'eunuch', 'minister_eunuch_entry');
      }
      return order;
    }
    if (targetCharacter === 'maid') {
      if (hasEvidence('handwritingHint') || turns.maid >= 1) {
        addInterjection(order, 'emperor', 'maid_emperor_reconsider');
      }
      return order;
    }
    if (targetCharacter === 'eunuch') {
      if (hasEvidence('palaceEntryRecord') || turns.eunuch >= 1) {
        addInterjection(order, 'minister', 'eunuch_minister_rebuttal');
      }
      if (hasEvidence('palaceEntryRecord')) {
        addInterjection(order, 'emperor', 'eunuch_emperor_entry', true);
      }
      return order;
    }
    if (targetCharacter === 'emperor') {
      if (!hasEvidence('ledgerClue') || !hasEvidence('palaceEntryRecord')) {
        addInterjection(order, 'minister', 'emperor_minister_deflect', true);
      }
      return order;
    }
    return order;
  };

  const applyAgentResult = (speaker, message) => {
    appendSceneTurn(message.role || speaker, message.content);

    const allowedFlagBySpeaker = {
      minister: ['ministerContradictionFound', 'ministerLedgerSuppressed'],
      maid: ['maidHandwritingHint'],
      eunuch: ['eunuchEntryRecord'],
      emperor: 'emperorTrust',
    };
    const allowedFlags = []
      .concat(allowedFlagBySpeaker[speaker] || [])
      .filter(Boolean);
    const stateUpdates = message.stateUpdates || {};
    for (const [rawFlagId, rawValue] of Object.entries(stateUpdates)) {
      const flagId = normalizeFlagId(rawFlagId);
      if (allowedFlags.includes(flagId) && typeof rawValue === 'boolean') {
        markFlag(flagId, rawValue);
      }
    }

    const evidenceUpdates = Array.isArray(message.evidenceUpdates)
      ? message.evidenceUpdates
      : [];
    for (const evidence of evidenceUpdates) {
      if (typeof evidence === 'string') {
        markEvidence(evidence);
      }
    }
    if (sceneMemory.value.flags.maidHandwritingHint) {
      markEvidence('handwritingHint');
    }
    if (sceneMemory.value.flags.eunuchEntryRecord) {
      markEvidence('palaceEntryRecord');
    }
    if (sceneMemory.value.flags.ministerLedgerSuppressed) {
      markEvidence('ledgerClue');
    }

    if (npcMemory.value[speaker]) {
      npcMemory.value[speaker].lastClaims.push(message.content);
      npcMemory.value[speaker].lastClaims = npcMemory.value[speaker].lastClaims.slice(-4);
    }
    updateStoryStage();
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
    if (suggestedNextNode === 'final_judgement' && !sceneMemory.value.flags.finalJudgementReady) {
      pushSystemMessage('证据链尚未完整，暂不能进入最终裁断。');
      return { applied: false, reason: 'EVIDENCE_INCOMPLETE' };
    }
    if (suggestedNextNode === node.nodeId || storyState.value.completedNodes.includes(suggestedNextNode)) {
      pushSystemMessage(`系统已忽略重复剧情跳转：${suggestedNextNode}`);
      return { applied: false, reason: 'REPEATED_TRANSITION' };
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
    pendingSuggestedNextNode.value = suggestedNextNode;
    pushSystemMessage('已触发新的剧情进展，请先阅读当前对话，再点击“继续”。');
    return { applied: true, reason: 'PENDING' };
  };

  return {
    storyState,
    sceneMemory,
    npcMemory,
    currentStage,
    nodeDialogueVisible,
    pendingSuggestedNextNode,
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
    hasEvidence,
    handleStoryCharacterClick,
    applySuggestedNextNode,
  };
}
