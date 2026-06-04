export const caseTruth = {
  title: '江南科场舞弊背后的皇子夺权案',
  summary:
    '江南科场舞弊表面是地方官员买卖功名，实际牵出皇子、边疆大将、户部亏空、边军粮草和盐商银票构成的暗线。血书密信是真的，但目前只能指向谋逆风险，仍需要笔迹、纸料、银两和出入记录补强证据链。',
  hiddenTruth:
    '张廷玉不是谋逆主犯。他压下关键证据，是为了先稳住朝局，避免太子、皇子、边军和江南官场同时失控。真正危险在皇子府与边疆军中的勾连。',
  playerMustProve: [
    '血书密信不是伪造的。',
    '江南科场舞弊与户部银两、边军粮草存在联系。',
    '张廷玉确实压下关键线索，但他是否是谋逆主犯还需进一步判断。',
  ],
};

export const npcProfiles = {
  emperor: {
    name: '玄烨',
    role: '皇帝、裁决者、压力源',
    goal: '观察玩家能否在威压下建立证据链，而不是空口指控皇子。',
    fear: '无证据牵连皇子会动摇国本；贸然公开会让朝局失控。',
    knows: [
      '张廷玉弹劾玩家。',
      '血书牵涉皇子，后果极重。',
      '江南案可能牵动国本。',
    ],
    hides: [
      '不会主动承认自己已经怀疑某位皇子。',
      '不会轻易透露密信是否已被内廷鉴别。',
      '不会替玩家补全证据链。',
    ],
    interjectsWhen: [
      '玩家说话莽撞时施压。',
      '玩家拿出证据链时态度缓和。',
      '张廷玉避重就轻时要求其正面回答。',
      '苏麻喇姑或李德全作证后重新审视密信。',
    ],
  },
  minister: {
    name: '张廷玉',
    role: '朝廷重臣、反对者、压制玩家的人',
    goal: '以朝局稳定为由压住案情，避免血书牵动皇子、边军与江南官场。',
    fear: '户部副账、皇子府门人和边军粮草线被串成证据链。',
    knows: [
      '江南科场舞弊牵涉户部银两。',
      '户部银两有一部分流向边军粮草。',
      '血书密信有可能是真的。',
      '有人希望玩家死在乾清宫前。',
      '自己曾压下过一份户部副账。',
    ],
    hides: [
      '曾经见过户部副账。',
      '知道血书不是普通伪造。',
      '入宫前见过一名皇子府上的门人。',
      '弹劾玩家是为了阻止案情失控，不完全是因为玩家有罪。',
    ],
    interjectsWhen: [
      '玩家证据链不完整时压制玩家。',
      '玩家拿出户部银两线索时动摇。',
      '李德全证实其行踪异常时转为强调大局。',
      '苏麻喇姑证明血书可信时无法继续简单否认。',
    ],
  },
  maid: {
    name: '苏麻喇姑',
    role: '宫廷老人、温和证人、礼法提醒者',
    goal: '保护皇帝判断，不让玩家用无证据的指控逼皇帝表态。',
    fear: '玩家莽撞牵连皇子，导致皇帝震怒并让旧事暴露。',
    knows: [
      '血书用语不像临时伪造。',
      '血书笔迹与旧日宫中一名被调往江南的内侍有关。',
      '玄烨真正忌讳无证据地牵连皇子。',
      '张廷玉确实压下某些东西。',
    ],
    hides: [
      '见过类似血书笔迹。',
      '知道皇帝已经私下命人验过密信纸料。',
      '知道某位皇子的乳母曾与江南官员有旧交。',
    ],
    interjectsWhen: [
      '玩家表现克制、忠诚、尊重证据。',
      '玩家问到血书笔迹、宫中旧人、密信纸料。',
      '张廷玉试图把血书完全定性为伪造。',
    ],
  },
  eunuch: {
    name: '李德全',
    role: '内廷消息节点、出入记录掌握者、谨慎提示者',
    goal: '在不卷入党争的前提下，给玩家关键旁证。',
    fear: '说出皇子府门人、密信调包或张廷玉行踪后被灭口。',
    knows: [
      '今夜乾清宫外谁来过。',
      '张廷玉入宫前见过谁。',
      '御案上的血书曾被人动过。',
      '有人想让玩家在面圣前失去辩解机会。',
      '皇帝仍在等证据。',
    ],
    hides: [
      '一名皇子府门人曾在乾清宫外出现。',
      '血书可能被调包过。',
      '张廷玉并非唯一接触密信的人。',
      '怕说太多被灭口。',
    ],
    interjectsWhen: [
      '玩家问到乾清宫出入、密信是否被动过、张廷玉何时入宫。',
      '玩家已经获得苏麻喇姑的部分提醒。',
      '皇帝或张廷玉的发言出现矛盾。',
    ],
  },
};

export const evidenceChain = {
  bloodLetter: {
    name: '血书密信',
    initial: true,
    source: '玩家初始持有',
    role: '指向皇子与边将勾结，但单独不能定罪。',
    unlocks: ['皇帝质疑血书真伪', '张廷玉攻击玩家伪造密信', '苏麻喇姑提醒血书不像临时伪造'],
  },
  handwritingHint: {
    name: '血书笔迹线索',
    initial: false,
    source: '苏麻喇姑',
    role: '证明血书并非普通伪造，指向旧日宫中内侍与江南案。',
    unlocks: ['苏麻喇姑作证', '皇帝好感上升', '张廷玉无法继续简单否认血书'],
  },
  palaceEntryRecord: {
    name: '乾清宫出入记录',
    initial: false,
    source: '李德全',
    role: '证明张廷玉入宫前见过皇子府门人，密信在玩家入宫前可能被动过。',
    unlocks: ['李德全插话', '张廷玉行踪矛盾', '皇帝开始怀疑张廷玉压下事实'],
  },
  ledgerClue: {
    name: '户部副账线索',
    initial: false,
    source: '追问张廷玉或通过李德全暗示',
    role: '证明江南科场案与户部银两相关，连接舞弊案和边军粮草。',
    unlocks: ['张廷玉第一次动摇', '皇帝要求解释户部银两', '张廷玉强调朝局稳定'],
  },
  borderArmyLink: {
    name: '边军粮草线索',
    initial: false,
    source: '张廷玉被逼问后松口，或通过户部副账解锁',
    role: '连接皇子、江南银两、边疆大将，是进入最终指控阶段的核心证据。',
    unlocks: ['张廷玉突破', '皇帝进入最终裁断', '玩家可以选择指控方向'],
  },
};

export const storyStages = {
  stage_1: {
    name: '天威压身',
    goal: '玩家先在皇帝震怒下表明立场。',
    nodes: ['prologue', 'eunuch_warn', 'emperor_strike', 'player_choice', 'minister_pressure'],
  },
  stage_2: {
    name: '自由审问初段',
    goal: '玩家分别试探四个 NPC，确认每个人的立场。',
    advanceWhen: '至少审问过两个 NPC，或获得 handwritingHint / palaceEntryRecord 任一线索。',
  },
  stage_3: {
    name: '证据链成形',
    goal: '把血书、户部银两、乾清宫出入记录串联起来。',
    advanceWhen: '获得 handwritingHint 或 palaceEntryRecord，或发现张廷玉矛盾。',
  },
  stage_4: {
    name: '张廷玉失守',
    goal: '张廷玉承认压下户部副账，但强调自己是为了朝局稳定。',
    advanceWhen: '同时具备 ledgerClue、palaceEntryRecord 和 ministerContradictionFound。',
  },
  stage_5: {
    name: '最终裁断',
    goal: '玩家选择指控方向，进入对应结局。',
    advanceWhen: '证据链足以支撑最终判断，尤其是 borderArmyLink 出现后。',
  },
};

export const interruptionRules = [
  {
    id: 'minister_emperor_pressure',
    target: 'minister',
    speaker: 'emperor',
    once: true,
    description: '审问大臣推进后，皇帝要求张廷玉正面回答。',
  },
  {
    id: 'minister_maid_handwriting',
    target: 'minister',
    speaker: 'maid',
    once: true,
    description: '张廷玉否认血书时，苏麻喇姑可从笔迹和宫中旧人角度提醒。',
  },
  {
    id: 'minister_eunuch_entry',
    target: 'minister',
    speaker: 'eunuch',
    once: true,
    description: '张廷玉行踪被追问时，李德全可补充乾清宫出入记录。',
  },
  {
    id: 'maid_emperor_reconsider',
    target: 'maid',
    speaker: 'emperor',
    once: true,
    description: '苏麻喇姑提供笔迹或纸料线索后，皇帝重新审视血书。',
  },
  {
    id: 'eunuch_minister_rebuttal',
    target: 'eunuch',
    speaker: 'minister',
    once: true,
    description: '李德全提到出入记录后，张廷玉试图以朝局大义反驳。',
  },
];

export const createInitialEvidenceState = () =>
  Object.fromEntries(
    Object.entries(evidenceChain).map(([id, evidence]) => [id, Boolean(evidence.initial)])
  );

export const createInitialInterrogationState = () => ({
  currentTarget: null,
  visitedCharacters: [],
  turnCounts: {
    emperor: 0,
    minister: 0,
    maid: 0,
    eunuch: 0,
  },
  triggeredInterjections: [],
});
