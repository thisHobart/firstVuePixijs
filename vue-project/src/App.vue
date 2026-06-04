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
      <h3>{{ currentNode.title }}</h3>
      <p>{{ storyPanelText }}</p>
      <p v-if="storyNotice" class="story-notice">{{ storyNotice }}</p>
      <div v-if="currentNode.type === 'player_input'" class="story-choice-list">
        <button
          v-for="choice in currentNode.choices"
          :key="choice.id"
          type="button"
          :disabled="dialogueLoading"
          @click="chooseStoryOption(choice)"
        >
          {{ choice.text }}
        </button>
      </div>
      <button
        v-if="canContinueStory"
        type="button"
        class="story-next-button"
        :disabled="dialogueLoading"
        @click="continueStory"
      >
        继续
      </button>
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

      <div v-if="availableConversationCharacters.length > 1" class="speaker-switcher">
        <button
          v-for="characterId in availableConversationCharacters"
          :key="characterId"
          type="button"
          :class="{ active: activeConversation === characterId }"
          :disabled="dialogueLoading || Boolean(pendingStoryNode)"
          @click="startConversation(characterId)"
        >
          {{ getCharacterName(characterId) }}
        </button>
      </div>

      <div class="input-container">
        <input
          v-model="playerInput"
          @keyup.enter="sendPlayerInput"
          :placeholder="dialogueLoading ? '对方正在回应……' : '你说……'"
          :disabled="Boolean(pendingStoryNode) || dialogueLoading"
        />
        <button
          @click="sendPlayerInput"
          :disabled="Boolean(pendingStoryNode) || dialogueLoading"
        >
          {{ dialogueLoading ? '等待中...' : '发送' }}
        </button>
        <button @click="toggleHistory" class="history-button">历史</button>
      </div>
    </div>
    <div v-else class="dialogue-box-placeholder">
      <p>{{ dialoguePlaceholderText }}</p>
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
import { useStoryState } from './composables/useStoryState';

const pixiCanvasContainer = ref(null);
const pixiApp = ref(null);
const characterStates = ref({});
const characterSprites = ref({});

// Dialogue state
const activeConversation = ref(null);
const playerInput = ref('');
const conversationHistory = ref([]);
const displayedStoryNodeIds = ref(new Set());
const showHistory = ref(false);
const dialogueLoading = ref(false);

// Authentication state
const currentUser = ref(null);
const authToken = ref(null);
const authMode = ref('login');
const authForm = ref({ username: '', password: '' });
const authError = ref('');
const authLoading = ref(false);

const isAuthenticated = computed(() => Boolean(currentUser.value && authToken.value));
const authTitle = computed(() => (authMode.value === 'login' ? '登录' : '注册'));

const authHeaders = (headers = {}) => {
  if (!authToken.value) return headers;
  return {
    ...headers,
    Authorization: `Bearer ${authToken.value}`,
  };
};

const getCharacterName = (id) => {
  const character = characterPresets.find(c => c.id === id);
  return character ? character.name : '';
};

const clearActiveConversationState = () => {
  activeConversation.value = null;
  playerInput.value = '';
  showHistory.value = false;
};

const {
  storyState,
  storyNotice,
  currentNode,
  getStoryContext,
  storyPanelText,
  canContinueStory,
  dialoguePlaceholderText,
  pendingStoryNode,
  continueStory,
  chooseStoryOption,
  appendSceneTurn,
  decideSpeakingOrder,
  applyAgentResult,
  handleStoryCharacterClick,
} = useStoryState(getCharacterName, {
  getCharacterFavorability: (characterId) => characterStates.value[characterId]?.favorability ?? 50,
  onStoryAdvanced: clearActiveConversationState,
  onStoryChoice: (choice) => {
    conversationHistory.value.push({ role: 'player', content: choice.text });
  },
});

const availableConversationCharacters = computed(() => {
  const node = currentNode.value;
  if (node?.type !== 'free_interaction') return [];
  return (node.availableCharacters || []).filter((characterId) => characterId !== 'player');
});

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
  clearActiveConversationState();
  conversationHistory.value = [];
  displayedStoryNodeIds.value = new Set();
};

const applyFavorabilityChanges = (changes = {}) => {
  Object.entries(changes).forEach(([characterId, rawDelta]) => {
    const target = characterStates.value[characterId];
    if (!target) return;
    const delta = Number.isFinite(Number(rawDelta))
      ? Math.max(-5, Math.min(5, Math.trunc(Number(rawDelta))))
      : 0;
    if (delta !== 0) {
      target.favorability += delta;
    }
  });
};

const appendStoryNodeToHistory = (node, options = {}) => {
  if (!node?.nodeId || !node.text) return;
  const includeClickNpc = Boolean(options.includeClickNpc);
  if (node.type === 'click_npc' && !includeClickNpc) return;
  if (displayedStoryNodeIds.value.has(node.nodeId)) return;

  displayedStoryNodeIds.value.add(node.nodeId);
  const role = node.speaker && node.speaker !== 'system' ? node.speaker : 'system';
  conversationHistory.value.push({ role, content: node.text });
  appendSceneTurn(role, node.text);
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
      if (authMode.value === 'register' && response.status === 409) {
        authError.value = '用户名已经存在，请换一个用户名';
        return;
      }
      authError.value =
        (payload && (payload.detail || payload.message)) || '请求失败，请稍后重试';
      return;
    }
    if (!payload?.access_token) {
      authError.value = '登录响应缺少令牌，请稍后重试';
      return;
    }
    authToken.value = payload.access_token;
    currentUser.value = payload.username || username;
    authForm.value.password = '';
    resetConversationState();
    appendStoryNodeToHistory(currentNode.value);
  } catch (error) {
    console.error('auth request failed', error);
    authError.value = '无法连接服务器，请稍后重试';
  } finally {
    authLoading.value = false;
  }
};

const logout = () => {
  currentUser.value = null;
  authToken.value = null;
  authMode.value = 'login';
  authError.value = '';
  authForm.value.username = '';
  authForm.value.password = '';
  resetConversationState();
};

const markLatestPlayerMessageBlocked = () => {
  for (let index = conversationHistory.value.length - 1; index >= 0; index -= 1) {
    if (conversationHistory.value[index]?.role === 'player') {
      conversationHistory.value[index] = {
        ...conversationHistory.value[index],
        blocked: true,
      };
      return;
    }
  }
};

const fetchDialogueNode = async (character, speakingOrder = [], playerTurnToRecord = '') => {
  if (!isAuthenticated.value) return;
  if (conversationHistory.value.length === 0) return;

  console.log(
    "正在发送到后端的历史记录:",
    JSON.stringify(conversationHistory.value, null, 2)
  );
  try {
    // Construct history for backend, ensuring roles are 'user' or 'assistant'
    const backendHistory = conversationHistory.value
      .filter(msg => msg.role !== 'system' && !msg.blocked)
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
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        character: character,
        history: backendHistory,
        storyContext: getStoryContext(character, speakingOrder),
      }),
    });

    if (response.status === 401) {
      logout();
      throw new Error('登录已失效，请重新登录');
    }
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
    const inputGuard =
      !Array.isArray(data) && typeof data?.inputGuard === 'object' && data.inputGuard
        ? data.inputGuard
        : null;
    const favorabilityChanges =
      !Array.isArray(data) && typeof data?.favorabilityChanges === 'object' && data.favorabilityChanges
        ? data.favorabilityChanges
        : null;

    if (inputGuard?.allowed === false) {
      const guardMessage =
        typeof inputGuard.systemMessage === 'string' && inputGuard.systemMessage.trim()
          ? inputGuard.systemMessage.trim()
          : '当前输入无法进入剧情，请重新输入。';
      conversationHistory.value.push({
        role: 'system',
        content: guardMessage
      });
      markLatestPlayerMessageBlocked();
      return { applied: false, blocked: true };
    }

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

        return {
          role: resolvedRole,
          content: rawContent,
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

    if (playerTurnToRecord) {
      appendSceneTurn('player', playerTurnToRecord);
    }

    if (favorabilityChanges) {
      applyFavorabilityChanges(favorabilityChanges);
    }

    for (const message of normalizedMessages) {
      conversationHistory.value.push({
        role: message.role,
        content: message.content
      });

      const transition = applyAgentResult(character, message);
      if (transition.applied) return transition;
    }
    return { applied: false };
  } catch (error) {
    console.error('Fetch操作出现问题:', error);
    conversationHistory.value.push({
      role: 'system',
      content: `无法连接到服务器: ${error.message}`
    });
    return { applied: false };
  }
};

const startConversation = async (characterId) => {
  if (!isAuthenticated.value) return;
  if (dialogueLoading.value) return;
  if (characterId === 'player') return;
  const storyClick = handleStoryCharacterClick(characterId);
  if (!storyClick.allowed) {
    return;
  }
  if (storyClick.mode === 'story_dialogue') {
    appendStoryNodeToHistory(currentNode.value, { includeClickNpc: true });
    return;
  }
  if (activeConversation.value === characterId) return;
  activeConversation.value = characterId;
  playerInput.value = '';
  showHistory.value = false;
};

const sendPlayerInput = async () => {
  if (!isAuthenticated.value) return;
  if (dialogueLoading.value) return;
  if (pendingStoryNode.value) return;
  const trimmedInput = playerInput.value.trim();
  if (trimmedInput === '' || !activeConversation.value) return;

  dialogueLoading.value = true;
  conversationHistory.value.push({ role: 'player', content: trimmedInput });

  try {
    const speakingOrder = decideSpeakingOrder(activeConversation.value);
    for (const [index, speaker] of speakingOrder.entries()) {
      const transition = await fetchDialogueNode(
        speaker,
        speakingOrder,
        index === 0 ? trimmedInput : ''
      );
      if (transition?.applied || transition?.blocked) break;
    }
  } finally {
    dialogueLoading.value = false;
    playerInput.value = '';
  }
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

watch(authToken, (value) => {
  if (typeof window === "undefined") return;
  try {
    if (value) {
      window.localStorage.setItem("authToken", value);
    } else {
      window.localStorage.removeItem("authToken");
    }
  } catch (_) {}
});

watch(
  () => storyState.value.currentNodeId,
  () => {
    appendStoryNodeToHistory(currentNode.value);
    updateCharacterFocus();
  }
);

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
  characterSprites.value = {};

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
    characterSprites.value[character.id] = sprite;
    stage.addChild(sprite);
  });
  updateCharacterFocus();
}

const updateCharacterFocus = () => {
  const node = currentNode.value;
  Object.entries(characterSprites.value).forEach(([id, sprite]) => {
    if (id === 'player' || !node || (!node.lockedCharacter && !node.availableCharacters?.length)) {
      sprite.alpha = 1;
      return;
    }
    const isAllowed = node.lockedCharacter
      ? id === node.lockedCharacter
      : node.availableCharacters.includes(id);
    sprite.alpha = isAllowed ? 1 : 0.3;
  });
}

onMounted(async () => {
  if (typeof window !== "undefined") {
    try {
      const savedUser = window.localStorage.getItem("authUsername");
      const savedToken = window.localStorage.getItem("authToken");
      if (savedUser && savedToken) {
        authToken.value = savedToken;
        currentUser.value = savedUser;
        const response = await fetch('/api/auth/profile', {
          headers: authHeaders(),
        });
        if (!response.ok) {
          logout();
        }
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
  appendStoryNodeToHistory(currentNode.value);
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

.story-notice {
  margin-top: 8px;
  color: #9a1f1f;
  font-weight: 600;
}

.story-choice-list {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.story-choice-list button,
.story-next-button {
  padding: 8px 12px;
  border: 1px solid #8a6530;
  background: #6d3f12;
  color: #fff7dd;
  cursor: pointer;
  font-size: 14px;
}

.story-choice-list button {
  flex: 1;
  text-align: left;
}

.story-choice-list button:hover,
.story-next-button:hover {
  background: #8b541d;
}

.story-next-button {
  margin-top: 10px;
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

.speaker-switcher {
  display: flex;
  gap: 8px;
  margin: 0 0 12px;
}

.speaker-switcher button {
  padding: 6px 12px;
  border: 1px solid #777;
  border-radius: 5px;
  background: #2d2d2d;
  color: #fff;
  cursor: pointer;
}

.speaker-switcher button.active {
  border-color: #f0c54f;
  background: #6d3f12;
  color: #fff7dd;
}

.speaker-switcher button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
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
