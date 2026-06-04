import { computed, ref } from 'vue';
import {
  caseTruth,
  createInitialEvidenceState,
  createInitialInterrogationState,
  evidenceChain,
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
  const pendingStoryNode = ref(null);

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
    if (pendingStoryNode.value) return true;
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
      lockedCharacter: node.lockedCharacter,
      availableCharacters: node.availableCharacters || [],
      completedNodes: storyState.value.completedNodes,
      playerChoices: storyState.value.playerChoices,
      currentStageId: storyState.value.currentStageId,
      currentStage: currentStage.value,
      interrogationState: storyState.value.interrogation,
      targetCharacter,
      speakingOrder,
      sceneMemory: {
        summary: sceneMemory.value.summary,
        recentTurns: sceneMemory.value.recentTurns.slice(-8),
        evidence: sceneMemory.value.evidence,
        flags: sceneMemory.value.flags,
      },
      npcMemory: Object.fromEntries(
        Object.entries(npcMemory.value).map(([id, memory]) => [
          id,
          {
            stance: memory.stance,
            lastClaims: memory.lastClaims.slice(-3),
          },
        ])
      ),
    };
  };

  const pushSystemMessage = (content) => {
    storyNotice.value = content;
  };

  const advanceStory = (nextNodeId) => {
    if (!storyNodes[nextNodeId]) return;
    pendingStoryNode.value = null;
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
    if (pendingStoryNode.value) {
      advanceStory(pendingStoryNode.value);
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

  const textIncludesAny = (text, keywords) => {
    const normalizedText = String(text || '').toLowerCase();
    return keywords.some((keyword) => normalizedText.includes(keyword.toLowerCase()));
  };

  const inferProgressFromDialogue = (speaker, text) => {
    const changed = {
      evidence: [],
      flags: [],
    };
    const markEvidenceChange = (evidenceId) => {
      if (markEvidence(evidenceId)) changed.evidence.push(evidenceId);
    };
    const markFlagChange = (flagId) => {
      if (markFlag(flagId, true)) changed.flags.push(flagId);
    };

    if (
      speaker === 'maid' &&
      textIncludesAny(text, ['笔迹', '纸料', '旧日', '内侍', '江南的内侍', '不像临时伪造'])
    ) {
      markFlagChange('maidHandwritingHint');
      markEvidenceChange('handwritingHint');
    }

    if (
      speaker === 'eunuch' &&
      textIncludesAny(text, ['入宫', '乾清宫外', '偏门', '门人', '出入', '动过', '血书被'])
    ) {
      markFlagChange('eunuchEntryRecord');
      markEvidenceChange('palaceEntryRecord');
    }

    if (
      speaker === 'minister' &&
      textIncludesAny(text, ['户部', '副账', '账册', '银两', '压下', '粮草'])
    ) {
      markFlagChange('ministerLedgerSuppressed');
      markEvidenceChange('ledgerClue');
    }

    if (
      speaker === 'minister' &&
      textIncludesAny(text, ['臣为大局', '大局', '老臣确曾', '确曾', '压下'])
    ) {
      markFlagChange('ministerContradictionFound');
    }

    if (
      hasEvidence('ledgerClue') &&
      textIncludesAny(text, ['边军', '边疆', '粮草', '大将', '军中'])
    ) {
      markEvidenceChange('borderArmyLink');
    }

    return changed;
  };

  const suggestStoryProgress = () => {
    const node = currentNode.value;
    if (!node || node.type !== 'free_interaction' || pendingStoryNode.value) {
      return { applied: false, reason: 'NO_TRANSITION' };
    }
    const canSuggest = (nodeId) =>
      (node.nextNodes || []).includes(nodeId) &&
      storyNodes[nodeId] &&
      !storyState.value.completedNodes.includes(nodeId);

    let nextNode = null;
    if (sceneMemory.value.flags.finalJudgementReady && canSuggest('final_judgement')) {
      nextNode = 'final_judgement';
    } else if (
      (
        hasEvidence('handwritingHint') ||
        hasEvidence('palaceEntryRecord') ||
        hasEvidence('ledgerClue')
      ) &&
      canSuggest('evidence_chain_forming')
    ) {
      nextNode = 'evidence_chain_forming';
    } else if (
      (sceneMemory.value.flags.ministerContradictionFound || sceneMemory.value.flags.ministerLedgerSuppressed) &&
      canSuggest('minister_breakthrough')
    ) {
      nextNode = 'minister_breakthrough';
    } else if (hasEvidence('handwritingHint') && canSuggest('maid_testimony')) {
      nextNode = 'maid_testimony';
    } else if (hasEvidence('palaceEntryRecord') && canSuggest('eunuch_secret')) {
      nextNode = 'eunuch_secret';
    }

    if (!nextNode) return { applied: false, reason: 'NO_TRANSITION' };
    pendingStoryNode.value = nextNode;
    pushSystemMessage('剧情状态已满足新的推进条件，请先阅读当前对话，再点击“继续”。');
    return { applied: true, reason: 'STATE_MACHINE_PENDING' };
  };

  const applyAgentResult = (speaker, message) => {
    if (isFreeInteraction.value) {
      recordInterrogationTurn(speaker);
    }
    appendSceneTurn(message.role || speaker, message.content);

    inferProgressFromDialogue(speaker, message.content);

    if (npcMemory.value[speaker]) {
      npcMemory.value[speaker].lastClaims.push(message.content);
      npcMemory.value[speaker].lastClaims = npcMemory.value[speaker].lastClaims.slice(-4);
    }
    updateStoryStage();
    return suggestStoryProgress();
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

  return {
    storyState,
    sceneMemory,
    npcMemory,
    currentStage,
    nodeDialogueVisible,
    pendingStoryNode,
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
  };
}
