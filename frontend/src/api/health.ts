import { API_BASE_URL, HEALTH_TIMEOUT_MS } from '../config'

export interface HealthResponse {
  status: 'ok'
}

export async function getHealth(signal: AbortSignal): Promise<HealthResponse> {
  const controller = new AbortController()
  let timer: ReturnType<typeof setTimeout> | undefined
  let cancel = () => {}

  const interrupted = new Promise<never>((_, reject) => {
    cancel = () => {
      controller.abort()
      reject(new Error('Backend unavailable'))
    }
    signal.addEventListener('abort', cancel, { once: true })
    timer = setTimeout(cancel, HEALTH_TIMEOUT_MS)
    if (signal.aborted) cancel()
  })

  const request = async (): Promise<HealthResponse> => {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      credentials: 'omit',
      redirect: 'error',
    })
    if (response.status !== 200) throw new Error('Backend unavailable')
    const body: unknown = await response.json()
    if (typeof body !== 'object' || body === null || !('status' in body) || body.status !== 'ok') {
      throw new Error('Backend unavailable')
    }
    return { status: 'ok' }
  }

  try {
    return await Promise.race([interrupted, request()])
  } finally {
    clearTimeout(timer)
    signal.removeEventListener('abort', cancel)
  }
}
