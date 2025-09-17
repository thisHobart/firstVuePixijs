import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,   // 等价于 '0.0.0.0'，监听所有网卡
    port: 5173    // 可改成其他端口，比如 3000
  }
})