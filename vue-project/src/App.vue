<template>
  <div class="pixi_app_container">
    <h1>古代互动小说：宫廷风云</h1>
    <h2>场景：金銮殿</h2>
    <div ref="pixiCanvasContainer" class="canvas-container"></div>

    <div v-if="activeConversation" class="dialogue-box">
      <p class="speaker-name">{{ currentSpeakerName }}</p>
      <p class="dialogue-text" @click="handleDialogueClick">{{ currentDialogueText }}</p>

      <!-- Choices replaced by input field -->
      <div class="input-container">
        <input v-model="playerInput" @keyup.enter="sendPlayerInput" placeholder="你说……" />
        <button @click="sendPlayerInput">发送</button>
      </div>
    </div>
    <div v-else class="dialogue-box-placeholder">
      <p>点击NPC开始对话</p>
    </div>
  </div>
</template>

<script setup>
import * as PIXI from 'pixi.js';
import { onMounted, ref, computed } from 'vue';
import { characterPresets } from './assets/characterPresets';

const pixiCanvasContainer = ref(null);
const pixiApp = ref(null);

// Dialogue state
const activeConversation = ref(null);
const currentDialogueNode = ref(null);
const playerInput = ref(''); // New ref for player input

const currentSpeakerName = computed(() => {
  const speakerId = currentDialogueNode.value?.speaker;
  if (speakerId === 'system') return '系统提示';
  return characterPresets.find(c => c.id === speakerId)?.name || '';
});

const currentDialogueText = computed(() => {
  return currentDialogueNode.value?.text || '';
});

const fetchDialogueNode = async (character, node) => {
  if (!node) return; // Do not send empty requests
  try {
    const response = await fetch('http://127.0.0.1:8000/api/dialogue', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ character, node }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    currentDialogueNode.value = data;
  } catch (error) {
    console.error('There was a problem with the fetch operation:', error);
    endConversation();
  }
};

const startConversation = async (characterId) => {
  if (characterId === 'player' || activeConversation.value) return;
  activeConversation.value = characterId;
  await fetchDialogueNode(characterId, 'start');
};

const sendPlayerInput = async () => {
  if (playerInput.value.trim() === '') return;
  await fetchDialogueNode(activeConversation.value, playerInput.value.trim());
  playerInput.value = '';
};

const endConversation = () => {
  activeConversation.value = null;
  currentDialogueNode.value = null;
}

const handleDialogueClick = async () => {
    // This function can be used for advancing dialogue if there are no choices/inputs needed
    // For now, the main interaction is via the input field.
    const nextNodeId = currentDialogueNode.value?.nextNode;
    if (nextNodeId && !currentDialogueNode.value?.choices?.length) { // Only advance if no choices
        await fetchDialogueNode(activeConversation.value, nextNodeId);
    } else if (!nextNodeId && !currentDialogueNode.value?.choices?.length) {
        // endConversation(); // Decide if clicking ends conversation
    }
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
  initPixiApp();
  setupScene();
});
</script>

<style>
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

.dialogue-box, .dialogue-box-placeholder {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 800px; /* Wider for input */
  min-height: 150px; /* Taller for input */
  background-color: rgba(0, 0, 0, 0.8);
  border: 2px solid #fff;
  border-radius: 10px;
  color: #fff;
  padding: 15px 20px;
  box-sizing: border-box;
  font-size: 18px;
}
.dialogue-box-placeholder {
    text-align: center;
    padding-top: 20px;
    font-style: italic;
    color: #36d78c;
}

.speaker-name {
  font-weight: bold;
  color: #f0c54f;
  margin: 0 0 10px 0;
}

.dialogue-text {
  margin: 0 0 15px 0;
  cursor: pointer;
}

.input-container {
  display: flex;
  gap: 10px;
  margin-top: 10px;
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
</style>
