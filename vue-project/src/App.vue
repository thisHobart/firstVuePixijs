<template>
  <div class="pixi_app_container">
    <h1>PixiJS角色自定义示例</h1>
    <form @submit.prevent="handleSubmit" class="role-form">
      <label>
        姓名：
        <input v_model="mainCharacter.name" placeholder="请输入名字" required></input>
      </label>
    </form>
    <div ref="pixiCanvasContainer"></div>
  </div>
</template>

<script setup>
import * as PIXI from 'pixi.js';
import { onMounted, ref, } from 'vue';
const pixiCanvasContainer = ref(null);
const pixiApp = ref(null);

onMounted(() => {
  initPixiApp();
})

const initPixiApp = async () => {
  const container = pixiCanvasContainer.value;
  const app = new PIXI.Application();
  await app.init({
    width: 800,
    height: 600,
    backgroundColor: "#3bc39a"
  })
  pixiApp.value = app;
  container.appendChild(pixiApp.value.canvas);
}
</script>

<style>
.foo {
  background-color: #3bc39a;
}

.pixi_app_container {
  background-color: #f0f0f0;
}
</style>