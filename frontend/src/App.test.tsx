import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './HealthStatus'
import { HEALTH_TIMEOUT_MS } from './config'

function response(body: unknown = { status: 'ok' }, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

describe('backend connection page', () => {
  it('shows loading until a validated HTTP 200 arrives through the API prefix', async () => {
    let finish!: (value: Response) => void
    const fetchMock = vi.fn(() => new Promise<Response>((resolve) => { finish = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    expect(screen.getByRole('status')).toHaveTextContent('Checking backend…')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeDisabled()
    await act(async () => { finish(response()) })
    expect(screen.getByRole('status')).toHaveTextContent('Backend reachable')
    expect(fetchMock).toHaveBeenCalledWith('/api/health', expect.objectContaining({
      signal: expect.any(AbortSignal), cache: 'no-store', credentials: 'omit', redirect: 'error',
    }))
  })

  it.each([201, 204, 404, 500, 503])('reports HTTP %s as unavailable', async (status) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status })))
    render(<App />)
    expect(await screen.findByText('Backend unavailable')).toBeVisible()
  })

  it.each([null, [], 'ok', {}, { status: 'down' }, { status: 1 }])('rejects invalid body %j', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(body)))
    render(<App />)
    expect(await screen.findByText('Backend unavailable')).toBeVisible()
  })

  it('reports malformed JSON without showing raw response details', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private error details')))
    render(<App />)
    expect(await screen.findByText('Backend unavailable')).toBeVisible()
    expect(screen.queryByText(/private error details/)).not.toBeInTheDocument()
  })

  it('reports network failure without exposing the exception', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('private network details')))
    render(<App />)
    expect(await screen.findByText('Backend unavailable')).toBeVisible()
    expect(screen.queryByText(/private network details/)).not.toBeInTheDocument()
  })

  it('bounds a stalled response and aborts it after five seconds', async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn((_url: string, _options: RequestInit) => new Promise<Response>(() => {}))
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    await act(async () => { await vi.advanceTimersByTimeAsync(HEALTH_TIMEOUT_MS) })
    expect(screen.getByText('Backend unavailable')).toBeVisible()
    expect(fetchMock.mock.calls[0][1].signal!.aborted).toBe(true)
    expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled()
  })

  it('also bounds a stalled JSON body after headers arrive', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status: 200, json: () => new Promise(() => {}) }))
    render(<App />)
    await act(async () => { await vi.advanceTimersByTimeAsync(HEALTH_TIMEOUT_MS) })
    expect(screen.getByText('Backend unavailable')).toBeVisible()
  })

  it('clears stale success on retry, handles failure and recovers', async () => {
    let finish!: (value: Response) => void
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response())
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve }))
      .mockResolvedValueOnce(response())
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    await screen.findByText('Backend reachable')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(screen.getByText('Checking backend…')).toBeVisible()
    expect(screen.queryByText('Backend reachable')).not.toBeInTheDocument()
    await act(async () => { finish(response({}, 503)) })
    expect(await screen.findByText('Backend unavailable')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('Backend reachable')).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('aborts outstanding work on unmount', () => {
    const fetchMock = vi.fn((_url: string, _options: RequestInit) => new Promise<Response>(() => {}))
    vi.stubGlobal('fetch', fetchMock)
    const view = render(<App />)
    const signal = fetchMock.mock.calls[0][1].signal!
    expect(signal.aborted).toBe(false)
    view.unmount()
    expect(signal.aborted).toBe(true)
  })

  it('ignores late success from a timed-out request after a retry', async () => {
    vi.useFakeTimers()
    let finish!: (value: Response) => void
    vi.stubGlobal('fetch', vi.fn()
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve }))
      .mockRejectedValueOnce(new Error('offline')))
    render(<App />)
    await act(async () => { await vi.advanceTimersByTimeAsync(HEALTH_TIMEOUT_MS) })
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await act(async () => { finish(response()) })
    expect(screen.getByText('Backend unavailable')).toBeVisible()
    expect(screen.queryByText('Backend reachable')).not.toBeInTheDocument()
  })
})
