import { useEffect, useRef, useState } from 'react'
import HealthStatus from './HealthStatus'
import EmployeeWorkspace, { Conversation, Records } from './EmployeeWorkspace'
import type { RecordItem } from './EmployeeWorkspace'
import { theme } from '../config/theme'
import { ApiError, demoRequest, STARTER } from './api/demo'
import type { Answer, Catalog, Current, Dashboard, Employee, Metric, ReportPage, Source } from './api/demo'

const roleLabel = { manager: 'Manager', employee: 'Employee', hr_admin: 'HR/Admin' }
function initials(name: string) { return name.split(' ').map(x => x[0]).slice(0, 2).join('') }
function dateLabel(value: string | null) { return value ? new Date(`${value}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not recorded' }
function remember(value: number | null) { try { if (value === null) localStorage.removeItem('demo.employee_id'); else localStorage.setItem('demo.employee_id', String(value)) } catch { /* Memory-only selection remains available. */ } }
function saved(): number | null { try { const value = localStorage.getItem('demo.employee_id'); return value !== null && /^-?\d+$/.test(value) ? Number(value) : null } catch { return null } }

function MetricCard({ title, metric }: { title: string; metric: Metric }) {
  const noun = title === 'Assigned tasks' ? 'tasks' : 'training records'
  return <section className="metric-card"><p className="eyebrow">{title}</p>
    <div className={`metric-value ${metric.completion_pct === null ? 'unavailable' : ''}`}>{metric.completion_pct === null ? (metric.total === 0 ? `No assigned ${noun}` : `No eligible ${noun}`) : `${metric.completion_pct}%`}{metric.completion_pct !== null && <span>completed</span>}</div>
    <div className="progress-track"><div style={{ width: `${metric.completion_pct ?? 0}%` }} /></div>
    <p>{metric.completed} of {metric.denominator} eligible records · {metric.total} total</p>
    <div className="status-list">{Object.entries(metric.statuses).map(([label, count]) => <span key={label}>{label} <b>{count}</b></span>)}</div>
    <small>{metric.definition}</small>
  </section>
}
function Sources({ values }: { values: Source[] }) {
  return <div className="source-list">{values.length === 0 ? <p className="muted">No evidence records are available.</p> : values.map(source => <article className="source" key={source.record_id}>
    <div><span className="tag">{source.record_type === 'project_tasks' ? 'Task' : 'Training'}</span><strong>{source.label || 'Untitled record'}</strong></div>
    <p>{source.status} · {source.date_label}: {dateLabel(source.date)}</p><code>{source.record_id}</code>
  </article>)}</div>
}
function TextList({ title, values }: { title: string; values: string[] }) {
  return values.length > 0 ? <div className="answer-section"><h4>{title}</h4><ul>{values.map((value, i) => <li key={i}>{value}</li>)}</ul></div> : null
}

function Workspace({ actor, onInvalid }: { actor: Current; onInvalid: () => void }) {
  const [reports, setReports] = useState<Employee[]>([])
  const [cursor, setCursor] = useState<number | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [reportError, setReportError] = useState('')
  const [loadingReports, setLoadingReports] = useState(true)
  const [retry, setRetry] = useState(0)
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [dashboardError, setDashboardError] = useState('')
  const [dashboardRetry, setDashboardRetry] = useState(0)
  const [tab, setTab] = useState<'overview' | 'assistant'>('overview')
  const [workRecords,setWorkRecords] = useState<RecordItem[]>([])
  const [question, setQuestion] = useState(STARTER)
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [chatError, setChatError] = useState('')
  const [busy, setBusy] = useState(false)
  const [submitted, setSubmitted] = useState('')
  const requests = useRef(new Set<AbortController>())
  const chat = useRef<AbortController | null>(null)
  const actorId = actor.persona.employee_id
  function failure(error: unknown) {
    if (error instanceof ApiError && (error.status === 401 || error.code === 'invalid_demo_request')) onInvalid()
    return error instanceof Error ? error.message : 'Request failed.'
  }
  useEffect(() => () => { for (const request of requests.current) request.abort(); chat.current?.abort() }, [])
  useEffect(() => {
    const controller = new AbortController()
    setLoadingReports(true); setReportError(''); setReports([])
    void demoRequest<ReportPage>('/manager/reports', actorId, controller.signal).then(page => {
      if (!controller.signal.aborted) { setReports(page.reports); setCursor(page.next_after_employee_id); setLoadingReports(false) }
    }).catch(error => { if (!controller.signal.aborted) { setReportError(failure(error)); setLoadingReports(false) } })
    return () => controller.abort()
  }, [actorId, retry])
  useEffect(() => {
    setWorkRecords([]); setDashboard(null); setDashboardError(''); setAnswer(null); setChatError(''); setBusy(false); setSubmitted(''); setQuestion(STARTER)
    chat.current?.abort()
    if (selected === null) return
    const controller = new AbortController()
    void demoRequest<Dashboard>(`/manager/reports/${selected}/dashboard`, actorId, controller.signal).then(data => {
      if (!controller.signal.aborted) setDashboard(data)
    }).catch(error => { if (!controller.signal.aborted) setDashboardError(failure(error)) })
    void demoRequest<{records:RecordItem[]}>(`/manager/reports/${selected}/record`, actorId, controller.signal).then(data=>{if(!controller.signal.aborted)setWorkRecords(data.records)}).catch(error=>{if(!controller.signal.aborted)setDashboardError(failure(error))})
    return () => controller.abort()
  }, [actorId, selected, dashboardRetry])
  async function loadMore() {
    const controller = new AbortController(); requests.current.add(controller)
    setLoadingReports(true); setReportError('')
    try {
      const page = await demoRequest<ReportPage>(`/manager/reports?after_employee_id=${cursor}`, actorId, controller.signal)
      if (!controller.signal.aborted) { setReports(old => [...old, ...page.reports]); setCursor(page.next_after_employee_id) }
    } catch (error) { if (!controller.signal.aborted) setReportError(failure(error)) }
    finally { requests.current.delete(controller); if (!controller.signal.aborted) setLoadingReports(false) }
  }
  async function ask() {
    if (selected === null || busy) return
    const controller = new AbortController(); chat.current = controller
    setBusy(true); setChatError(''); setAnswer(null); setSubmitted(question)
    try {
      const data = await demoRequest<Answer>(`/manager/reports/${selected}/chat`, actorId, controller.signal, question)
      if (!controller.signal.aborted) setAnswer(data)
    } catch (error) { if (!controller.signal.aborted) setChatError(failure(error)) }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }
  const filtered = reports.filter(e => `${e.display_name} ${e.position_title}`.toLowerCase().includes(search.toLowerCase()))
  return <div className="workspace">
    <aside className="team-panel"><div className="panel-heading"><div><p className="eyebrow">Your team</p><h2>Direct reports</h2></div><span className="count">{reports.length}{cursor !== null ? '+' : ''}</span></div>
      <label className="search-label"><span>Find in loaded reports</span><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search names or roles" /></label>
      <p className="scope-caption">Current reports · Active & Leave</p>
      {reportError && <div className="error" role="alert">{reportError}<button onClick={() => { setSelected(null); setRetry(x => x+1) }}>Retry reports</button></div>}
      {loadingReports && <p role="status">Loading reports…</p>}
      {!loadingReports && !reportError && filtered.length === 0 && <p className="muted">{reports.length ? 'No matching reports in this page.' : 'No eligible current direct reports.'}</p>}
      <div className="report-list">{filtered.map(employee => <button className={`report ${selected === employee.employee_id ? 'selected' : ''}`} key={employee.employee_id} onClick={() => { if (selected !== employee.employee_id) { setDashboard(null); setAnswer(null); setSelected(employee.employee_id) }; setTab('overview') }}>
        <span className="avatar">{initials(employee.display_name)}</span><span><strong>{employee.display_name}</strong><small>{employee.position_title}</small></span><span aria-hidden="true">›</span>
      </button>)}</div>
      {cursor !== null && <button className="secondary more" onClick={() => void loadMore()} disabled={loadingReports}>Load more reports</button>}
    </aside>
    <div className="detail-panel">
      {selected === null ? <section className="welcome"><span className="welcome-mark">↗</span><p className="eyebrow">A thoughtful conversation starts here</p><h2>Prepare with context.</h2><p>Select a direct report to explore their recorded work and prepare an evidence-grounded conversation.</p><div className="journey"><span>01 · Select a report</span><span>02 · Explore progress</span><span>03 · Prepare a conversation</span></div></section> : dashboardError ? <section className="error" role="alert">{dashboardError}<button onClick={() => setDashboardRetry(x => x+1)}>Retry overview</button></section> : !dashboard ? <section role="status" className="empty">Loading employee overview…</section> : <>
        <header className="employee-header"><span className="avatar large">{initials(dashboard.employee.display_name)}</span><div><p className="eyebrow">Employee overview</p><h2>{dashboard.employee.display_name}</h2><p>{dashboard.employee.position_title}</p><p className="muted">{dashboard.employee.department_name ?? 'Department not recorded'} · {dashboard.team_name ?? 'Team not recorded'}</p></div><span className={`tag ${dashboard.employee.employment_status === 'Active' ? 'active' : 'leave'}`}>{dashboard.employee.employment_status}</span></header>
        <div className="employee-meta"><span>Joined <b>{dateLabel(dashboard.hire_date)}</b></span><span>In role since <b>{dateLabel(dashboard.role_start_date)}</b></span><span>Read from PostgreSQL <b>{dateLabel(dashboard.as_of)}</b></span></div>
        <nav className="tabs" aria-label="Employee view"><button className={tab==='overview' ? 'current' : ''} onClick={() => setTab('overview')}>Overview</button><button className={tab==='assistant' ? 'current' : ''} onClick={() => setTab('assistant')}>Review preparation <span>✦</span></button></nav>
        {tab === 'overview' ? <div className="tab-content"><div className="section-heading"><div><h3>Recorded progress</h3><p>All-time factual summaries · not performance ratings</p></div><button onClick={() => setTab('assistant')}>Prepare a conversation ↗</button></div>
          <div className="metrics"><MetricCard title="Assigned tasks" metric={dashboard.tasks} /><MetricCard title="Training & development" metric={dashboard.training} /></div>
          <section className="evidence-panel"><h3>Goals and completed training</h3><p className="muted">Adapted from Kevin’s recent-wins pattern, using available PostgreSQL goals and training. Goal dates are recorded plan dates, not confirmed achievement dates.</p><Records records={workRecords.filter(r=>r.category==='goals' || r.status==='Completed').sort((a,b)=>(b.date??'').localeCompare(a.date??'')).slice(0,8)} /></section><section className="evidence-panel"><h3>Evidence snapshot</h3><p className="muted">Up to 8 most recently created tasks and 8 most recently assigned training records. Completion dates stay unknown when absent.</p><Sources values={dashboard.sources} /></section>
          <details className="limitations"><summary>Data coverage & limitations</summary><ul>{dashboard.data_gaps.map(x => <li key={x}>{x}</li>)}</ul></details>
        </div> : <div className="tab-content assistant-panel"><div className="section-heading"><div><p className="eyebrow">✦ Manager preparation</p><h3>Bring the evidence into the conversation.</h3></div></div><Conversation key={selected} actorId={actorId} subjectId={selected} manager /><details><summary>Existing task and training summary</summary><p className="muted">This evidence summary supports one question type: task and training progress. Each request stands alone; prior answers are not sent to the assistant.</p>
          <button className="starter" onClick={() => setQuestion(STARTER)}>{STARTER} ↗</button>
          <form onSubmit={e => { e.preventDefault(); void ask() }}><label htmlFor="question">Your question about {dashboard.employee.display_name}</label><textarea id="question" maxLength={500} value={question} onChange={e => setQuestion(e.target.value)} /><div className="composer-footer"><small>Only task and training evidence is permitted.</small><button disabled={busy || !question.trim()} type="submit">{busy ? 'Preparing…' : 'Prepare answer ↗'}</button></div></form>
          {busy && <p role="status">Retrieving scoped records and preparing an answer…</p>}{chatError && <div role="alert" className="error">{chatError}</div>}
          {answer && <article className="answer"><div className="answer-top"><span className="tag">{answer.mode === 'simulated' ? 'Simulated answer · real database evidence' : `${answer.mode === 'azure' ? 'Azure OpenAI' : 'OpenAI'} answer · validated source IDs`}</span></div><p className="asked">{submitted}</p><h3>Conversation brief</h3><p>{answer.answer}</p><TextList title="Conversation starters" values={answer.suggested_approach} /><TextList title="Strengths to explore" values={answer.strengths_to_acknowledge} /><TextList title="Data gaps" values={answer.data_gaps} /><details open><summary>Source records ({answer.sources.length})</summary><Sources values={answer.sources} /></details><small>{answer.scope_note}</small></article>}</details>
        </div>}
      </>}
    </div>
  </div>
}

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [candidate, setCandidate] = useState<number | null>(saved)
  const [current, setCurrent] = useState<Current | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [resolving, setResolving] = useState(false)
  const [workspace,setWorkspace]=useState<'self'|'manager'>('self')
  function clear() { setCandidate(null); setCurrent(null); remember(null) }
  useEffect(() => {
    const controller = new AbortController(); setCatalog(null); setError(''); setCurrent(null)
    void demoRequest<Catalog>('/demo/personas', null, controller.signal).then(value => {
      if (controller.signal.aborted) return
      setCatalog(value)
      setCandidate(old => { if (old !== null && !value.personas.some(p => p.employee_id === old)) { remember(null); return null }; return old })
    }).catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
    return () => controller.abort()
  }, [attempt])
  useEffect(() => {
    setCurrent(null)
    if (candidate === null || catalog === null) return
    const controller = new AbortController(); setResolving(true); setError('')
    void demoRequest<Current>('/demo/me', candidate, controller.signal).then(value => {
      if (!controller.signal.aborted) { setCurrent(value); setResolving(false); remember(value.persona.employee_id) }
    }).catch(reason => {
      if (!controller.signal.aborted) { setError(reason.message); setResolving(false); if (reason instanceof ApiError && (reason.status === 401 || reason.status === 422)) clear() }
    })
    return () => controller.abort()
  }, [candidate, catalog])
  return <div className="app-shell"><header className="app-header"><a className="brand" href="#" onClick={e => { e.preventDefault(); clear() }}><span className="brand-icon">{theme.brand.mark}</span><span>{theme.brand.name}<span className="brand-sub">{theme.brand.descriptor}</span></span></a><span className="environment">SYNTHETIC DATA DEMO</span><details className="health-menu"><summary>Connection status</summary><HealthStatus /></details></header>
    <div className="demo-banner"><strong>Demo identity</strong> — anyone can select these synthetic personas; this is not authentication.</div>
    <div className="identity-bar"><div><p className="eyebrow">Workspace</p><h1>Your employee and manager workspace</h1></div><div className="persona-controls"><label htmlFor="persona">Demo persona</label><select id="persona" value={candidate ?? ''} onChange={e => { setCurrent(null); setCandidate(e.target.value === '' ? null : Number(e.target.value)); remember(null) }} disabled={!catalog}><option value="">Select a persona</option>{catalog?.personas.map(p => <option key={p.employee_id} value={p.employee_id}>{p.display_name} · {roleLabel[p.role]}</option>)}</select>{candidate !== null && <button className="text-button" onClick={clear}>Clear selection</button>}</div></div>
    <main className="app-main">{error && <div className="error" role="alert">{error}<button onClick={() => setAttempt(x => x+1)}>Retry connection</button></div>}{!catalog && !error && <p role="status">Loading demo personas…</p>}{resolving && candidate !== null && catalog && !current && !error && <p role="status">Resolving selected persona…</p>}{catalog && catalog.personas.length === 0 && <div className="empty">No Active synthetic personas are available.</div>}
      {current ? <><div className="session-line"><span>Viewing as <b>{current.persona.display_name}</b> · {roleLabel[current.persona.role]}</span><span>{catalog?.assistant_available ? `${catalog.assistant_mode === 'azure' ? 'Azure OpenAI' : 'OpenAI'} configured · scoped database records` : 'AI not configured · database records available'}</span></div><nav className="tabs" aria-label="Workspace"><button className={workspace==='self'?'current':''} onClick={()=>setWorkspace('self')}>My workspace</button>{current.persona.role==='manager'&&<button className={workspace==='manager'?'current':''} onClick={()=>setWorkspace('manager')}>My direct reports</button>}</nav>{workspace==='manager'&&current.persona.role==='manager'?<Workspace key={current.persona.employee_id} actor={current} onInvalid={clear}/>:<EmployeeWorkspace key={current.persona.employee_id} actor={current}/>}</> : catalog && !error && !resolving && <section className="welcome"><span className="welcome-mark">↗</span><p className="eyebrow">Evidence for better conversations</p><h2>Make room for a meaningful review.</h2><p>Choose a synthetic persona to explore their own record. Managers also have a workspace for current direct reports.</p><div className="journey"><span>Read-only corporate data</span><span>Scoped direct reports</span><span>Traceable evidence</span></div></section>}
    </main><footer className="app-footer"><span>{theme.brand.name} · Capstone demonstration</span><span>Preparation support. Human judgment stays with you.</span></footer></div>
}
