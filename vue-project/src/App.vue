<template>
  <div class="pixi_app_container">
    <h1>古代互动小说：宫廷风云</h1>
    <h2>场景：金銮殿</h2>
    <div ref="pixiCanvasContainer" class="canvas-container"></div>
    <div class="dialogue-box">
      <p>{{ currentDialogue }}</p>
    </div>
  </div>
</template>

<script setup>
import * as PIXI from 'pixi.js';
import { onMounted, ref } from 'vue';
import { characterPresets } from './assets/characterPresets';
import { dialogueData } from './dialogue.js';

const pixiCanvasContainer = ref(null);
const pixiApp = ref(null);
const currentDialogue = ref("点击角色开始对话。"); // Updated placeholder

onMounted(() => {
  initPixiApp();
  setupScene();
})

const showDialogue = (characterId) => {
  const dialogue = dialogueData[characterId]?.greeting;
  if (dialogue) {
    const characterName = characterPresets.find(c => c.id === characterId)?.name;
    currentDialogue.value = `${characterName}: "${dialogue}"`;
  }
}

const initPixiApp = () => {
  const container = pixiCanvasContainer.value;
  const app = new PIXI.Application({
    width: 800,
    height: 600,
    backgroundColor: 0x1a1a1a, // A darker, more serious background
  });
  pixiApp.value = app;
  container.appendChild(app.view);
}

const setupScene = () => {
  if (!pixiApp.value) return;

  const stage = pixiApp.value.stage;
  stage.removeChildren(); // Clear previous sprites

  const positions = [
    { x: 400, y: 150 }, // Emperor in the center top
    { x: 200, y: 350 }, // Minister on the left
    { x: 600, y: 350 }, // Eunuch on the right
    { x: 400, y: 450 }, // Maid in the front
  ];

  characterPresets.forEach((character, index) => {
    const sprite = character.createContainer();
    sprite.position.set(positions[index].x, positions[index].y);

    // Make sprite interactive
    sprite.interactive = true;
    sprite.buttonMode = true; // Show a pointer cursor on hover
    sprite.on('pointerdown', () => showDialogue(character.id));

    stage.addChild(sprite);
  });
}
</script>

<style>
.pixi_app_container {
  position: relative;
  text-align: center;
  background-color: #f0f0f0;
}

.canvas-container {
  display: inline-block;
}

.dialogue-box {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 760px;
  min-height: 100px;
  background-color: rgba(0, 0, 0, 0.7);
  border: 2px solid #fff;
  border-radius: 10px;
  color: #fff;
  padding: 10px 20px;
  text-align: left;
  font-size: 18px;
  box-sizing: border-box;
}
</style>
