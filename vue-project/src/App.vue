<template>
  <div class="pixi_app_container">
    <div v-if="isAuthenticated" class="auth-status-bar">
      <span>当前用户：{{ currentUser }}</span>
      <button type="button" @click="logout">退出登录</button>
    </div>

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
    <section class="intro-panel">
      <h3>序章：初入金銮殿</h3>
      <p>{{ introText }}</p>
    </section>
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

    <div v-if="!isAuthenticated" class="auth-overlay">
      <div class="auth-card">
        <h2>{{ authTitle }}</h2>
        <form class="auth-form" @submit.prevent="submitAuth">
          <label>
            用户名
            <input
              v-model.trim="authForm.username"
              type="text"
              placeholder="请输入用户名"
              autocomplete="username"
              :disabled="authLoading"
            />
          </label>
          <label>
            密码
            <input
              v-model="authForm.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              :disabled="authLoading"
            />
          </label>
          <p v-if="authError" class="auth-error">{{ authError }}</p>
          <button type="submit" :disabled="authLoading">
            {{ authLoading ? '提交中...' : authTitle }}
          </button>
        </form>
        <p class="auth-toggle">
          <span>{{ authMode === 'login' ? '还没有账号？' : '已经有账号了？' }}</span>
          <button type="button" @click="toggleAuthMode">
            {{ authMode === 'login' ? '去注册' : '去登录' }}
          </button>
        </p>
      </div>
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
const introText =
  '你是新科状元，初入朝堂。今日奉旨入宫，在金銮殿外等候召见。' +
  '皇帝玄烨正在殿中议事，张廷玉侍立一旁，苏麻喇姑在殿侧候命，李德全负责传旨。' +
  '这是你第一次真正接触宫廷权力中心，你的每一句话都可能影响他人对你的看法。';

// Dialogue state
const activeConversation = ref(null);
const playerInput = ref('');
const conversationHistory = ref([]);
const showHistory = ref(false);

// Authentication state
const currentUser = ref(null);
const authMode = ref('login');
const authForm = ref({ username: '', password: '' });
const authError = ref('');
const authLoading = ref(false);

const isAuthenticated = computed(() => Boolean(currentUser.value));
const authTitle = computed(() => (authMode.value === 'login' ? '登录' : '注册'));

const getCharacterName = (id) => {
  const character = characterPresets.find(c => c.id === id);
  return character ? character.name : '';
};

const getSpeakerName = (role) => {
  if (role === 'system') return '系统提示';
  const character = characterPresets.find(c => c.id === role);
  return character ? character.name : '玩家'; // 玩家身份标识
};

const lastMessage = computed(() => {
  return conversationHistory.value[conversationHistory.value.length - 1];
});

const toggleHistory = () => {
  showHistory.value = !showHistory.value;
};

const toggleAuthMode = () => {
  authMode.value = authMode.value === 'login' ? 'register' : 'login';
  authError.value = '';
  authForm.value.password = '';
};

const resetConversationState = () => {
  activeConversation.value = null;
  conversationHistory.value = [];
  playerInput.value = '';
  showHistory.value = false;
};

const submitAuth = async () => {
  if (authLoading.value) return;
  authError.value = '';
  const username = authForm.value.username.trim();
  authForm.value.username = username;
  const password = authForm.value.password;
  if (!username || !password) {
    authError.value = '请输入用户名和密码';
    return;
  }
  authLoading.value = true;
  try {
    const response = await fetch(`/api/auth/${authMode.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    let payload = null;
    try {
      payload = await response.json();
    } catch (_) {
      payload = null;
    }
    if (!response.ok) {
      authError.value =
        (payload && (payload.detail || payload.message)) || '请求失败，请稍后重试';
      return;
    }
    currentUser.value = (payload && payload.username) || username;
    authForm.value.password = '';
    resetConversationState();
  } catch (error) {
    console.error('auth request failed', error);
    authError.value = '无法连接服务器，请稍后重试';
  } finally {
    authLoading.value = false;
  }
};

const logout = () => {
  currentUser.value = null;
  authMode.value = 'login';
  authError.value = '';
  authForm.value.username = '';
  authForm.value.password = '';
  resetConversationState();
};

const fetchDialogueNode = async (character) => {
  if (!isAuthenticated.value) return;
  if (conversationHistory.value.length === 0) return;

  console.log(
    "正在发送到后端的历史记录:",
    JSON.stringify(conversationHistory.value, null, 2)
  );
  try {
    // Construct history for backend, ensuring roles are 'user' or 'assistant'
    const backendHistory = conversationHistory.value
      .filter(msg => msg.role !== 'system')
      .map(msg => ({
        role: msg.role === 'player' ? 'user' : 'assistant',
        content: msg.content
      }));

    console.log(
      '转换后的后端历史记录:',
      JSON.stringify(backendHistory, null, 2)
    );

    const response = await fetch('/api/dialogue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character: character,
        history: backendHistory
      }),
    });

    if (!response.ok) throw new Error(`网络响应错误: ${response.statusText}`);

    const cloned = response.clone();
    const data = await response.json();
    console.log('后端返回的原始数据:', data);
    try {
      console.log('后端返回的原始文本:', await cloned.text());
    } catch (_) {}

    const messages = Array.isArray(data)
      ? data
      : Array.isArray(data?.messages)
        ? data.messages
        : [];

    if (!Array.isArray(messages) || messages.length === 0) {
      console.warn('后端响应为空或格式不符合预期:', data);
      conversationHistory.value.push({
        role: 'system',
        content: '未收到来自后端的有效回复，请稍后再试。'
      });
      return;
    }

    const normalizedMessages = messages
      .map((message) => {
        if (!message) return null;

        // 优先使用后端规范中的 text 字段，避免误用请求里 content 字段
        let rawContent = '';
        if (typeof message === 'string') {
          rawContent = message;
        } else if (typeof message === 'object') {
          if (typeof message.text === 'string') {
            rawContent = message.text;
          } else if (typeof message.content === 'string') {
            rawContent = message.content;
          }
        }
        if (!rawContent) {
          console.warn('忽略内容为空的后端消息:', message);
          return null;
        }

        const backendRole =
          (typeof message === 'object' && (message.role || message.speaker))
            || 'assistant';
        const resolvedRole =
          backendRole === 'assistant' && character
            ? character
            : backendRole;

        const favorabilityDelta =
          typeof message?.favorabilityChange === 'number'
            ? message.favorabilityChange
            : 0;

        return {
          role: resolvedRole,
          content: rawContent,
          favorabilityChange: favorabilityDelta,
        };
      })
      .filter(Boolean);

    if (normalizedMessages.length === 0) {
      console.warn('后端响应未包含可用的消息内容:', data);
      conversationHistory.value.push({
        role: 'system',
        content: '后端返回的对话内容为空。'
      });
      return;
    }

    for (const message of normalizedMessages) {
      conversationHistory.value.push({
        role: message.role,
        content: message.content
      });

      const favorabilityTarget = characterStates.value[character];
      if (favorabilityTarget && message.favorabilityChange !== 0) {
        favorabilityTarget.favorability += message.favorabilityChange;
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
  if (!isAuthenticated.value) return;
  if (characterId === 'player' || activeConversation.value) return;
  activeConversation.value = characterId;
  conversationHistory.value = [];
};

const sendPlayerInput = async () => {
  if (!isAuthenticated.value) return;
  const trimmedInput = playerInput.value.trim();
  if (trimmedInput === '' || !activeConversation.value) return;

  conversationHistory.value.push({ role: 'player', content: trimmedInput });

  await fetchDialogueNode(activeConversation.value);
  playerInput.value = '';
};

const endConversation = () => {
  resetConversationState();
}

watch(currentUser, (value) => {
  if (typeof window === "undefined") return;
  try {
    if (value) {
      window.localStorage.setItem("authUsername", value);
    } else {
      window.localStorage.removeItem("authUsername");
    }
  } catch (_) {}
});

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
  if (typeof window !== "undefined") {
    try {
      const savedUser = window.localStorage.getItem("authUsername");
      if (savedUser) {
        currentUser.value = savedUser;
      }
    } catch (_) {}
  }

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

.intro-panel {
  width: 820px;
  margin: 0 auto 12px;
  padding: 12px 18px;
  box-sizing: border-box;
  background: rgba(255, 248, 220, 0.92);
  border: 1px solid #c7a35a;
  color: #3d2a16;
  text-align: left;
}

.intro-panel h3 {
  margin: 0 0 6px;
  font-size: 17px;
  color: #6d3f12;
}

.intro-panel p {
  margin: 0;
  line-height: 1.7;
  font-size: 15px;
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

/* Authentication */
.auth-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.75);
  z-index: 200;
}

.auth-card {
  width: 320px;
  padding: 24px;
  background: #1f1f1f;
  border-radius: 12px;
  border: 1px solid #444;
  color: #fff;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.auth-card h2 {
  margin: 0 0 16px 0;
  text-align: center;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.auth-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}

.auth-form input {
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #555;
  background: #2a2a2a;
  color: #fff;
}

.auth-form button {
  margin-top: 8px;
  padding: 10px;
  background-color: #2c5b7c;
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
}

.auth-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-error {
  margin: 0;
  color: #ff6b6b;
  font-size: 13px;
}

.auth-toggle {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.auth-toggle button {
  background: none;
  border: none;
  color: #f0c54f;
  cursor: pointer;
  padding: 0;
}

.auth-status-bar {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #fff;
  display: flex;
  gap: 12px;
  align-items: center;
  z-index: 20;
}

.auth-status-bar button {
  background: transparent;
  border: 1px solid #fff;
  color: #fff;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.auth-status-bar button:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
