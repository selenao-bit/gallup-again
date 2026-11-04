// @vitest-environment node
import { realpathSync, mkdtempSync, mkdirSync, copyFileSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { resolveConfig } from 'vite'

describe('root npm configuration', () => {
  it('keeps frontend roots, assets, output and dotenv isolated', async () => {
    // A replica uses dummy values only; never reads or modifies private dotenv files.
    const root = realpathSync(mkdtempSync(join(tmpdir(), 'task101-vite-')))
    const frontend = join(root, 'frontend')
    mkdirSync(join(frontend, 'config'), { recursive: true })
    const source = fileURLToPath(new URL('../', import.meta.url))
    for (const file of ['vite.config.ts', 'config/api-prefix.ts', 'config/theme.ts']) {
      copyFileSync(join(source, file), join(frontend, file))
    }
    writeFileSync(join(root, '.env'), 'VITE_PRIVATE_SENTINEL=must-not-load\nVITE_API_BASE_URL=/private-root\nBACKEND_PROXY_TARGET=http://private.invalid\n')
    writeFileSync(join(frontend, '.env'), 'VITE_API_BASE_URL=/public-api\nBACKEND_PROXY_TARGET=http://127.0.0.1:8001\n')
    try {
      // Native loader resolves the copied config's imports through the real package.
      // Link dependencies only in the disposable fixture.
      const { symlinkSync } = await import('node:fs')
      symlinkSync(fileURLToPath(new URL('../../node_modules', import.meta.url)), join(root, 'node_modules'))
      const config = await resolveConfig({ configFile: join(frontend, 'vite.config.ts'), configLoader: 'native' }, 'build', 'production')
      expect(config.root).toBe(frontend)
      expect(config.envDir).toBe(frontend)
      expect(config.publicDir).toBe(join(frontend, 'public'))
      expect(config.build.outDir).toBe('dist')
      expect(config.env.VITE_PRIVATE_SENTINEL).toBeUndefined()
      expect(config.env.VITE_API_BASE_URL).toBe('/public-api')
      expect(config.env.BACKEND_PROXY_TARGET).toBeUndefined()
      expect(config.envPrefix).toBe('VITE_')
      const proxy = config.server.proxy?.['^/public-api(?:/|$)']
      expect(proxy).toMatchObject({ target: 'http://127.0.0.1:8001' })
      if (typeof proxy === 'object') expect(proxy.rewrite?.('/public-api/health')).toBe('/health')
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
