import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    // Element Plus 目前是全量引入（main.js: app.use(ElementPlus)），单 chunk 约 855 kB。
    // 已通过 manualChunks 把 ECharts/Vue/marked 拆开，最大业务包从 1.13 MB 降下来；
    // 阈值放到 900 kB 是有意为之，彻底消除需改成按需引入（unplugin-vue-components），见 README 演进项。
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
          if (id.includes('element-plus')) return 'element-plus'
          if (id.includes('marked')) return 'marked'
          return 'vendor'
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})