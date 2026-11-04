export function apiPrefix(value = '/api'): string {
  const prefix = value.replace(/\/+$/, '')
  if (!/^\/[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/.test(prefix)) {
    throw new Error('VITE_API_BASE_URL must be a relative path such as /api')
  }
  return prefix
}
