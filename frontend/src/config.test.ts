import { describe, expect, it } from 'vitest'
import { apiPrefix } from '../config/api-prefix'

describe('public API prefix', () => {
  it('defaults to /api and normalizes a trailing slash', () => {
    expect(apiPrefix()).toBe('/api')
    expect(apiPrefix('/local/api/')).toBe('/local/api')
  })

  it.each(['', '/', '//example.com', 'https://example.com', '/api?key=value', '/api/../private'])('rejects %j', (value) => {
    expect(() => apiPrefix(value)).toThrow('relative path')
  })
})
