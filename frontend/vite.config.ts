import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'
import { apiPrefix } from './config/api-prefix.ts'
import { theme, themeCss } from './config/theme.ts'

const frontendDirectory = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, frontendDirectory, ['VITE_', 'BACKEND_PROXY_TARGET'])
  const prefix = apiPrefix(env.VITE_API_BASE_URL)
  return {
    root: frontendDirectory,
    envDir: frontendDirectory,
    envPrefix: 'VITE_',
    plugins: [
      react(),
      {
        name: 'application-theme',
        transformIndexHtml: {
          order: 'pre',
          handler: (html) => ({
            html: html.replace('__APP_NAME__', theme.brand.name),
            tags: [
              { tag: 'meta', attrs: { name: 'application-name', content: theme.brand.name }, injectTo: 'head' },
              { tag: 'meta', attrs: { name: 'description', content: theme.brand.description }, injectTo: 'head' },
              { tag: 'meta', attrs: { name: 'theme-color', content: theme.color.primary }, injectTo: 'head' },
              { tag: 'style', attrs: { id: 'app-theme' }, children: themeCss, injectTo: 'head' },
            ],
          }),
        },
      },
    ],
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      proxy: {
        [`^${prefix}(?:/|$)`]: {
          target: env.BACKEND_PROXY_TARGET || 'http://127.0.0.1:8000',
          rewrite: (path) => path.slice(prefix.length),
        },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test-setup.ts'],
      clearMocks: true,
    },
  }
})
