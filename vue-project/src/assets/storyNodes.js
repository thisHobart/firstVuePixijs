export const storyNodes = {
  prologue: {
    nodeId: 'prologue',
    title: '序章：深夜密诏',
    type: 'narration',
    speaker: 'system',
    text: '已经是子时，乾清宫内烛火摇曳。你手按佩刀站在殿中央，空气沉重得让人窒息。御案上那封血书，今晚将决定半个朝廷的生死。',
    lockedCharacter: null,
    availableCharacters: [],
    autoNext: 'eunuch_warn',
  },

  eunuch_warn: {
    nodeId: 'eunuch_warn',
    title: '引路：李德全的暗示',
    type: 'click_npc',
    speaker: 'eunuch',
    text: '哎哟我的小祖宗，您可算来了。万岁爷今晚砸了三个茶盏……张廷玉大人死保太子，苏麻姑姑面色也不对。一会儿回话，千万掂量着点！',
    lockedCharacter: 'eunuch',
    availableCharacters: ['eunuch'],
    nextNodes: ['emperor_strike'],
  },

  emperor_strike: {
    nodeId: 'emperor_strike',
    title: '天威：玄烨的震怒',
    type: 'auto_dialogue',
    speaker: 'emperor',
    text: '这就是你查了三个月查出来的东西？！张廷玉折子上弹劾你“挟私报复、伪造密信陷害皇子”！你给朕解释解释！',
    lockedCharacter: 'emperor',
    availableCharacters: ['emperor'],
    effect: 'shake',
    autoNext: 'player_choice',
  },

  player_choice: {
    nodeId: 'player_choice',
    title: '抉择：侍卫的立场',
    type: 'player_input',
    speaker: 'player',
    text: '玄烨的目光压在你身上。血书、弹劾、皇子、边将，所有线索都在此刻逼你表态。',
    lockedCharacter: 'emperor',
    availableCharacters: ['emperor'],
    choices: [
      {
        id: 'defend_truth',
        text: '臣用性命担保，此信绝对真实，请皇上彻查皇子！',
        nextNode: 'minister_pressure',
      },
      {
        id: 'back_down',
        text: '臣……或许查证有误，求皇上恕罪。',
        nextNode: 'minister_pressure',
      },
    ],
  },

  minister_pressure: {
    nodeId: 'minister_pressure',
    title: '廷辩：张廷玉的敲打',
    type: 'auto_dialogue',
    speaker: 'minister',
    text: '皇上！此子狂妄！私信一出，国本动摇。小侍卫，你口口声声说有人谋反，证据链可完整？户部银两的去向你可查清了？若无铁证，你便是乱臣贼子！',
    lockedCharacter: 'minister',
    availableCharacters: ['minister'],
    autoNext: 'free_interrogation',
  },

  free_interrogation: {
    nodeId: 'free_interrogation',
    title: '破局：大殿暗流',
    type: 'free_interaction',
    speaker: null,
    text: '玄烨揉了揉太阳穴：“够了。朕给你们半个时辰。在这乾清宫内，你们各执一词。侍卫，你去说服张廷玉认罪，或者让苏麻姑姑替你作证。半个时辰后，拿不出铁证，推出去斩了！”',
    lockedCharacter: null,
    availableCharacters: ['emperor', 'minister', 'maid', 'eunuch'],
    nextNodes: [
      'evidence_chain_forming',
      'minister_breakthrough',
      'maid_testimony',
      'eunuch_secret',
      'final_judgement',
    ],
  },

  evidence_chain_forming: {
    nodeId: 'evidence_chain_forming',
    title: '证据：暗线初成',
    type: 'narration',
    speaker: 'system',
    text: '血书不再只是孤证。笔迹、出入记录或户部副账的碎片开始互相咬合，殿中众人的神色都变得谨慎起来。',
    lockedCharacter: null,
    availableCharacters: [],
    autoNext: 'free_interrogation',
  },

  minister_breakthrough: {
    nodeId: 'minister_breakthrough',
    title: '破局：张廷玉失守',
    type: 'narration',
    speaker: 'system',
    text: '张廷玉的神色终于出现一丝裂缝。他没有承认谋逆，却不得不承认自己见过户部副账，也曾压下过某些足以牵动朝局的线索。',
    lockedCharacter: null,
    availableCharacters: [],
    autoNext: 'free_interrogation',
  },

  maid_testimony: {
    nodeId: 'maid_testimony',
    title: '暗证：苏麻喇姑作证',
    type: 'narration',
    speaker: 'system',
    text: '苏麻喇姑轻叹一声，终于说出了一段旧事。她的话不重，却足以让玄烨重新审视那封血书。',
    lockedCharacter: null,
    availableCharacters: [],
    autoNext: 'free_interrogation',
  },

  eunuch_secret: {
    nodeId: 'eunuch_secret',
    title: '密闻：李德全吐露线索',
    type: 'narration',
    speaker: 'system',
    text: '李德全压低声音，说出今夜乾清宫外来客的名字。那名字像一枚暗钉，钉进所有人的心里。',
    lockedCharacter: null,
    availableCharacters: [],
    autoNext: 'free_interrogation',
  },

  final_judgement: {
    nodeId: 'final_judgement',
    title: '终局：御前裁断',
    type: 'player_input',
    speaker: 'player',
    text: '证据已在殿中铺开。玄烨没有急着追问皇子，而是先盯住张廷玉：“他压下副账，阻你查案。侍卫，你以为此罪当如何定？”',
    lockedCharacter: 'emperor',
    availableCharacters: ['emperor'],
    choices: [
      {
        id: 'minister_suppressed_evidence',
        text: '张廷玉压证属实，误国亦属重罪，但现有证据不足以定其为谋逆主犯。',
        nextNode: 'prince_investigation_order',
      },
      {
        id: 'accuse_minister',
        text: '张廷玉压下副账、包庇皇子，应以谋逆主犯论处。',
        nextNode: 'ending_minister_punished',
      },
      {
        id: 'accuse_prince_recklessly',
        text: '血书已足够，臣请皇上立刻拿问涉案皇子。',
        nextNode: 'ending_reckless_accusation',
      },
    ],
  },

  prince_investigation_order: {
    nodeId: 'prince_investigation_order',
    title: '密旨：转查皇子',
    type: 'narration',
    speaker: 'emperor',
    text: '玄烨沉默良久，终于缓缓开口：“张廷玉压证之罪，朕自会处置。你没有借势构陷重臣，也没有凭血书贸然逼朕拿问皇子，这很好。既然户部副账与兵部粮草底单已经相连，皇子府与边将往来，便由你暗中续查。”',
    lockedCharacter: null,
    availableCharacters: [],
    autoNext: 'ending_best_route',
  },

  ending_best_route: {
    nodeId: 'ending_best_route',
    title: '结局：暗授密查',
    type: 'narration',
    speaker: 'system',
    text: '证据链已成，玄烨采纳了你的密查之策。张廷玉暂退，户部副账与兵部粮草底单被密旨封存。乾清宫审问至此告一段落，你将奉旨暗查皇子府与边将往来。',
    lockedCharacter: null,
    availableCharacters: [],
  },

  ending_minister_punished: {
    nodeId: 'ending_minister_punished',
    title: '结局：重臣失势',
    type: 'narration',
    speaker: 'emperor',
    text: '张廷玉被革职候审，朝堂震动。你赢下了御前这一局，却隐约知道，真正的皇子暗线并未就此断绝。',
    lockedCharacter: null,
    availableCharacters: [],
  },

  ending_reckless_accusation: {
    nodeId: 'ending_reckless_accusation',
    title: '结局：慎刑司夜寒',
    type: 'narration',
    speaker: 'emperor',
    text: '玄烨的眼神冷了下去：“血书不是圣旨，猜疑也不是证据。”你被押出乾清宫，慎刑司的灯火在夜色中亮起。',
    lockedCharacter: null,
    availableCharacters: [],
  },
};
