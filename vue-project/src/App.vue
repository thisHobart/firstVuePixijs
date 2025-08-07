<template>
  <div class="pixi_app_container">
    <h1>PixiJS角色自定义示例</h1>
    <form @submit.prevent="handleSubmit" class="role-form">
      <label>
        姓名：
        <input v-model="mainChar.name" placeholder="请输入名字" required></input>
      </label>
      <button type="submit">保存角色</button>
    </form>
    <div ref="pixiCanvasContainer"></div>
    <h2>当前主角信息</h2>
    <pre>{{ mainChar }}</pre>
  </div>
</template>

<script setup>
import * as PIXI from 'pixi.js';
import { onMounted, ref } from 'vue';
import { characterPresets } from './assets/characterPresets';

const pixiCanvasContainer = ref(null);
const pixiApp = ref(null);
const mainChar = ref(characterPresets[0])

onMounted(() => {
  initPixiApp();
  handleSubmit();
})
function handleSubmit() {
  // 这里你可以做校验、提交后端、或重绘主角形象
  // 例如：清空舞台并重新绘制主角
  if (pixiApp.value) {
    pixiApp.value.stage.removeChildren()
    const sprite = mainChar.value.createContainer()
    sprite.position.set(300, 200)
    pixiApp.value.stage.addChild(sprite)
  }
  alert('角色信息已保存并同步到画面！')
}

const initPixiApp = () => {
  const container = pixiCanvasContainer.value;
  const app = new PIXI.Application({
    width: 800,
    height: 600,
    backgroundColor: 0x3bc39a // 注意v6用16进制数字
  });
  pixiApp.value = app;
  container.appendChild(app.view);
  const sprite = mainChar.value.createContainer();            // 创建该角色的精灵
  sprite.position.set(300, 200);                    // 设置显示位置（随你定）
  app.stage.addChild(sprite);                       // 添加到舞台上
}
</script>

<style>
label {
  display: block;
  margin-bottom: 6px;
}

.foo {
  background-color: #913815;
}

.pixi_app_container {
  background-color: #f0f0f0;
}
</style>
