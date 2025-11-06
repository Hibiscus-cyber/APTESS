import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/plugin/profile/gui/',  // 和 hook.py 保持一致
})
