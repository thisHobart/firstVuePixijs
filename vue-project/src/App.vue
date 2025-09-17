<template>
  <div class="pixi_app_container">
    <!-- Favorability display moved to top left -->
    <div class="favorability-status-container">
      <h3>角色好感度</h3>
      <ul>
        <li v-for="(status, id) in characterStates" :key="id">
          <span>{{ getCharacterName(id) }}: </span>
          <span>{{ status.favorability }}</span>
        </li>
      </ul>
    </div>

    <h1>古代互动小说：宫廷风云</h1>
    <h2>场景：金銮殿</h2>
    <div ref="pixiCanvasContainer" class="canvas-container"></div>

    <!-- Dialogue History Log -->
    <div v-if="showHistory" class="history-log-overlay" @click="toggleHistory">
      <div class="history-log-box" @click.stop>
        <h3>对话历史</h3>
        <div class="history-log-content">
          <div v-for="(message, index) in conversationHistory" :key="index" class="message">
            <p class="speaker-name">{{ getSpeakerName(message.role) }}:</p>
            <p class="dialogue-text">{{ message.content }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeConversation" class="dialogue-box">
      <!-- Display the last message -->
      <div class="last-message" v-if="lastMessage">
        <p class="speaker-name">{{ getSpeakerName(lastMessage.role) }}</p>
        <p class="dialogue-text">{{ lastMessage.content }}</p>
      </div>

      <div class="input-container">
        <input v-model="playerInput" @keyup.enter="sendPlayerInput" placeholder="你说……" />
        <button @click="sendPlayerInput">发送</button>
        <button @click="toggleHistory" class="history-button">历史</button>
      </div>
    </div>
    <div v-else class="dialogue-box-placeholder">
      <p>点击NPC开始对话</p>
    </div>
  </div>
</template>

<script setup>
import * as PIXI from 'pixi.js';
import { onMounted, ref, computed, nextTick, watch } from 'vue';
import { characterPresets } from './assets/characterPresets';

const pixiCanvasContainer = ref(null);
const pixiApp = ref(null);
const characterStates = ref({});

// Dialogue state
const activeConversation = ref(null);
const playerInput = ref('');
const conversationHistory = ref([]);
const showHistory = ref(false);

const getCharacterName = (id) => {
  const character = characterPresets.find(c => c.id === id);
  return character ? character.name : '';
};

const getSpeakerName = (role) => {
  if (role === 'system') return '系统提示';
  const character = characterPresets.find(c => c.id === role);
  return character ? character.name : '你'; // Default to '你' for player
};

const lastMessage = computed(() => {
  return conversationHistory.value[conversationHistory.value.length - 1];
});

const toggleHistory = () => {
  showHistory.value = !showHistory.value;
};

const fetchDialogueNode = async (character) => {
  if (conversationHistory.value.length === 0) return;

  console.log("正在发送到后端的历史记录:", JSON.stringify(conversationHistory.value, null, 2));
  try {
    // Construct history for backend, ensuring roles are 'user' or 'assistant'
    const backendHistory = conversationHistory.value.map(msg => ({
      role: msg.role === 'player' ? 'user' : 'assistant',
      content: msg.content
    }));

    const response = await fetch('/api/dialogue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character: character,
        history: backendHistory
      }),
    });

    if (!response.ok) throw new Error(`网络响应错误: ${response.statusText}`);

    const data = await response.json(); // Expects an array of messages

    for (const message of data) {
      conversationHistory.value.push({
        role: message.speaker || 'assistant',
        content: message.text
      });
      if (message.favorabilityChange && characterStates.value[character]) {
        characterStates.value[character].favorability += message.favorabilityChange;
      }
    }
  } catch (error) {
    console.error('Fetch操作出现问题:', error);
    conversationHistory.value.push({
      role: 'system',
      content: `无法连接到服务器: ${error.message}`
    });
  }
};

const startConversation = async (characterId) => {
  if (characterId === 'player' || activeConversation.value) return;
  activeConversation.value = characterId;
  conversationHistory.value = [{ role: 'player', content: '你好' }];
  await fetchDialogueNode(characterId);
};

const sendPlayerInput = async () => {
  const trimmedInput = playerInput.value.trim();
  if (trimmedInput === '' || !activeConversation.value) return;

  conversationHistory.value.push({ role: 'player', content: trimmedInput });

  await fetchDialogueNode(activeConversation.value);
  playerInput.value = '';
};

const endConversation = () => {
  activeConversation.value = null;
  conversationHistory.value = [];
  showHistory.value = false;
}

const initPixiApp = () => {
  const container = pixiCanvasContainer.value;
  const app = new PIXI.Application({
    width: 1024,
    height: 768,
    backgroundColor: 0xf1c588,
  });
  pixiApp.value = app;
  container.appendChild(app.view);
}

const setupScene = () => {
  if (!pixiApp.value) return;
  const stage = pixiApp.value.stage;
  stage.removeChildren();

  const positions = [
    { x: 400, y: 500 }, { x: 400, y: 150 }, { x: 200, y: 300 },
    { x: 600, y: 300 }, { x: 100, y: 450 },
  ];

  characterPresets.forEach((character, index) => {
    const sprite = character.createContainer();
    sprite.position.set(positions[index].x, positions[index].y);
    sprite.interactive = true;
    sprite.buttonMode = true;
    sprite.on('pointerdown', () => startConversation(character.id));
    stage.addChild(sprite);
  });
}

onMounted(() => {
  // Initialize character states from presets
  characterPresets.forEach(preset => {
    if (preset.id !== 'player') {
      characterStates.value[preset.id] = {
        favorability: preset.favorability
      };
    }
  });

  initPixiApp();
  setupScene();
});
</script>

<style>
/* General App Layout */
.pixi_app_container {
  position: relative;
  text-align: center;
  background-color: #f0f0f0;
  width: 1024px;
  margin: auto;
}

.canvas-container {
  display: inline-block;
}

/* Dialogue Box */
.dialogue-box, .dialogue-box-placeholder {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  min-height: 150px;
  background-color: rgba(0, 0, 0, 0.8);
  border: 2px solid #fff;
  border-radius: 10px;
  color: #fff;
  padding: 15px 20px;
  box-sizing: border-box;
  font-size: 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.dialogue-box-placeholder {
  justify-content: center;
  align-items: center;
  font-style: italic;
  color: #36d78c;
}

/* Last Message Display */
.last-message {
  margin-bottom: 15px;
}

.speaker-name {
  font-weight: bold;
  color: #f0c54f;
  margin: 0 0 5px 0;
}

.dialogue-text {
  margin: 0;
  white-space: pre-wrap; /* Allows text to wrap */
}

/* Input Controls */
.input-container {
  display: flex;
  gap: 10px;
}

.input-container input {
  flex-grow: 1;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #555;
  background-color: #333;
  color: #fff;
  font-size: 16px;
}

.input-container button {
  padding: 10px 20px;
  background-color: #4a4a4a;
  border: 1px solid #777;
  color: #fff;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 16px;
}

.input-container button:hover {
  background-color: #6a6a6a;
}

.history-button {
  background-color: #2c5b7c;
}
.history-button:hover {
  background-color: #3a7aab;
}

/* Favorability Status */
.favorability-status-container {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  border: 1px solid #fff;
  text-align: left;
  z-index: 10;
}

.favorability-status-container h3 {
  margin: 0 0 10px 0;
  color: #f0c54f;
  font-size: 16px;
  padding-bottom: 5px;
  border-bottom: 1px solid #555;
  text-align: center;
}

.favorability-status-container ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.favorability-status-container li {
  font-size: 14px;
  margin-bottom: 5px;
  white-space: nowrap;
}

/* History Log Overlay */
.history-log-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.history-log-box {
  width: 60%;
  max-width: 700px;
  height: 70%;
  background-color: #1a1a1a;
  border: 2px solid #f0c54f;
  border-radius: 15px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  color: #fff;
}

.history-log-box h3 {
  text-align: center;
  margin-top: 0;
  color: #f0c54f;
  border-bottom: 1px solid #555;
  padding-bottom: 10px;
}

.history-log-content {
  flex-grow: 1;
  overflow-y: auto;
  padding-right: 10px; /* For scrollbar spacing */
}

.history-log-content .message {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px dotted #444;
}
.history-log-content .message:last-child {
  border-bottom: none;
}
</style>
