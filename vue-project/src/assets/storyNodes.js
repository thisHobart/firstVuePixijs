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
    nextNodes: ['minister_breakthrough', 'maid_testimony', 'eunuch_secret'],
  },

  minister_breakthrough: {
    nodeId: 'minister_breakthrough',
    title: '破局：张廷玉失守',
    type: 'narration',
    speaker: 'system',
    text: '张廷玉的神色终于出现一丝裂缝。你抓住了证据链中最关键的一环，殿内风向开始变化。',
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
};
