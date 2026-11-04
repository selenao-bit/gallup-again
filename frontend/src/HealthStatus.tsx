import { useEffect, useState } from 'react'
import { getHealth } from './api/health'
import { theme } from '../config/theme'

type ConnectionStatus = 'loading' | 'reachable' | 'unavailable'

export default function HealthStatus() {
  const [attempt, setAttempt] = useState(0)
  const [status, setStatus] = useState<ConnectionStatus>('loading')

  useEffect(() => {
    const controller = new AbortController()
    void getHealth(controller.signal).then(
      () => { if (!controller.signal.aborted) setStatus('reachable') },
      () => { if (!controller.signal.aborted) setStatus('unavailable') },
    )
    return () => controller.abort()
  }, [attempt])

  function retry() {
    setStatus('loading')
    setAttempt((current) => current + 1)
  }

  return (
    <div className="health-status">
      <p className="eyebrow">Application foundation</p>
      <h1>{theme.brand.name}</h1>
      <p className="intro">Check the connection to the application backend.</p>
      <section aria-labelledby="connection-title">
        <h2 id="connection-title">Backend connection</h2>
        <div role="status" aria-live="polite" aria-atomic="true">
          <p className={`connection ${status}`}>
            {status === 'loading' && 'Checking backend…'}
            {status === 'reachable' && 'Backend reachable'}
            {status === 'unavailable' && 'Backend unavailable'}
          </p>
          <p>
            {status === 'loading' && 'Waiting for a response.'}
            {status === 'reachable' && 'The backend responded successfully.'}
            {status === 'unavailable' && 'The connection check failed. Check that the backend is running, then retry.'}
          </p>
        </div>
        <button type="button" onClick={retry} disabled={status === 'loading'}>Retry</button>
      </section>
      <p className="note">This check confirms backend HTTP availability only. Database connectivity is not checked.</p>
    </div>
  )
}
