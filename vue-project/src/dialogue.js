// dialogue.js

export const dialogueData = {
  emperor: {
    start: {
      speaker: 'emperor',
      text: "你就是新科状元？抬起头来，让朕瞧瞧。",
      choices: [
        { text: "（抬头，目光坚定）臣，XXX，参见皇上。", nextNode: 'emperor_response_1' },
        { text: "（叩首，谦卑恭敬）草民不知礼数，请皇上恕罪。", nextNode: 'emperor_response_2' }
      ]
    },
    emperor_response_1: {
      speaker: 'emperor',
      text: "嗯，不错，有几分胆识。朕喜欢有胆魄的年轻人。",
      nextNode: 'end' // Ends the conversation for now
    },
    emperor_response_2: {
      speaker: 'emperor',
      text: "不知者无罪，平身吧。繁文缛节，以后慢慢学就是了。",
      nextNode: 'end'
    },
    end: {
        speaker: 'system',
        text: '（与皇帝的对话结束）'
    }
  },
  minister: {
    start: {
      speaker: 'minister',
      text: "这位想必就是新科状元郎了，年少有为啊。",
      nextNode: 'end'
    },
    end: {
        speaker: 'system',
        text: '（与大臣的对话结束）'
    }
  },
  maid: {
    start: {
        speaker: 'maid',
        text: '状元郎，这边请。',
        nextNode: 'end'
    },
    end: {
        speaker: 'system',
        text: '（与宫女的对话结束）'
    }
  },
  eunuch: {
    start: {
        speaker: 'eunuch',
        text: '呦，状元郎，可喜可贺。',
        nextNode: 'end'
    },
    end: {
        speaker: 'system',
        text: '（与太监的对话结束）'
    }
  }
};
