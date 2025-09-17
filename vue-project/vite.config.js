import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,   // 等价于 '0.0.0.0'，监听所有网卡
    port: 5173,   // 可改成其他端口，比如 3000
    proxy: {
      // 通过 Vite 代理将前端的 /api 请求转发到本地后端
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
