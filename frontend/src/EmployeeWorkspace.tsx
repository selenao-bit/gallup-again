import { useEffect, useState } from 'react'
import { demoRequest } from './api/demo'
import type { Current, Employee } from './api/demo'
import { Q12_DISCUSS, Q12_SHORT } from './q12'

export interface RecordItem { record_id: string; category: string; title: string; status: string | null; date: string | null; fields: Record<string, string | number | boolean | null> }
interface Bundle { employee: Employee; records: RecordItem[]; counts: Record<string, number>; gaps: string[] }
interface AIAnswer { content: { answer: string; discussion_questions: string[]; data_gaps: string[]; cited_record_ids: string[] }; sources: RecordItem[] }
interface Message { email_id: number; thread_id: number; sender_id: number; sender_name: string; sent_at: string; subject: string | null; body: string; has_attachments: boolean; recipients: { recipient_id: number; recipient_type: string; name: string }[] }
interface Inbox { addresses: string[]; messages: Message[]; next_before: number | null; scope_note: string }
interface QItem { question_id: string; text: string; element: string; engagement_need: string; mean_score: number | null; top_box_pct: number | null; benchmark_pct: number | null; response_count: number; score_1_count: number; score_2_count: number; score_3_count: number; score_4_count: number; score_5_count: number }
interface Engagement { groups: {group_id:number; group_name:string; group_type:string}[]; surveys: {survey_id:number; reporting_period:string}[]; results: {group_id:number; survey_id:number; suppressed:boolean; items:QItem[]}[]; scope_note:string }
const tabs = ['My work and goals', 'My reviews', 'Team engagement (Q12)', 'Ask my record', "What is and isn't used"]
const questions = ['What goals did I have last year, and how did they turn out?', 'What did I say I wanted to develop in my self-assessments?', 'Which of my tasks were late, cancelled or needed revisions?', 'What training have I completed, and what is still open?']
const label = (s: string) => s.replaceAll('_', ' ').replace(/^./, x => x.toUpperCase())
const value = (v: unknown) => v == null ? 'Not recorded' : typeof v === 'boolean' ? v ? 'Yes' : 'No' : String(v)

export function Records({ records }: { records: RecordItem[] }) {
  return <div className="record-list">{!records.length && <p className="muted">No records are available in this category.</p>}{records.map(r => <details className="source" key={r.record_id}><summary><strong>{r.title}</strong> {r.status && <span className="tag">{r.status}</span>}<small> · {r.date?.slice(0,10) ?? 'Date not recorded'}</small></summary><dl className="record-fields">{Object.entries(r.fields).map(([k,v]) => <div key={k}><dt>{label(k)}</dt><dd>{value(v)}</dd></div>)}</dl><code>{r.record_id}</code></details>)}</div>
}
export function Conversation({ actorId, subjectId, manager=false, engagement=false, prompt }: { actorId:number; subjectId:number; manager?:boolean; engagement?:boolean; prompt?:string }) {
  const [question,setQuestion]=useState(prompt ?? '')
  const [answer,setAnswer]=useState<AIAnswer|null>(null)
  const [history,setHistory]=useState<{question:string;answer:AIAnswer}[]>([])
  const [draft,setDraft]=useState('')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [controller]=useState(() => new AbortController())
  useEffect(() => () => controller.abort(),[controller])
  async function ask() {
    setBusy(true); setError(''); setAnswer(null)
    try {
      const path=manager ? `/manager/reports/${subjectId}/conversation` : engagement ? '/employee/engagement/prepare' : '/employee/chat'
      const result=await demoRequest<AIAnswer>(path,actorId,controller.signal,question)
      if (controller.signal.aborted) return
      setAnswer(result); setHistory(h=>[...h,{question,answer:result}])
      setDraft(`Conversation preparation — editable draft\n\nContext and accomplishments\n${result.content.answer}\n\nDiscussion questions\n${result.content.discussion_questions.join('\n')}\n\nDevelopment, support and follow-up\n[Add your own agreed discussion points.]\n\nSources\n${result.sources.map(s=>`${s.record_id}: ${s.title}`).join('\n')}\n\nData gaps\n${result.content.data_gaps.join('\n')}`)
    } catch(e) { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Unable to prepare an answer.') }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }
  return <section><h3>{manager ? 'Start the Conversation' : engagement ? 'Prepare for a State of the Team conversation' : 'Ask questions about your own record'}</h3><p className="muted">On-demand answers use permitted records and cite their sources. Email is excluded from AI context. Each question is answered independently.</p>
    {!manager && !engagement && <div className="status-list">{questions.map(q=><button className="secondary" key={q} onClick={()=>setQuestion(q)}>{q}</button>)}</div>}
    <form onSubmit={e=>{e.preventDefault();void ask()}}><label>Your question or draft thoughts<textarea value={question} maxLength={2000} rows={5} onChange={e=>setQuestion(e.target.value)}/></label><button disabled={busy || !question.trim()}>{busy?'Reading permitted records…':engagement?'Help me prepare':'Prepare with AI'}</button></form>
    {error && <p className="error" role="alert">{error}</p>}
    {answer && <article className="answer"><span className="tag">AI answer · source IDs validated</span><p className="preserve-lines">{answer.content.answer}</p><h4>Discussion questions</h4><ul>{answer.content.discussion_questions.map((s,i)=><li key={i}>{s}</li>)}</ul><details><summary>Sources and coverage</summary><Records records={answer.sources}/><ul>{answer.content.data_gaps.map((s,i)=><li key={i}>{s}</li>)}</ul></details></article>}
    {manager && answer && <section><h3>Draft report</h3><p className="muted">Provisional preparation outline. Edit before using; this is not a completed performance review. Your edits remain in this browser session.</p><textarea aria-label="Editable draft report" rows={18} value={draft} onChange={e=>setDraft(e.target.value)}/><button className="secondary" onClick={()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([draft],{type:'text/plain'}));a.download='conversation-preparation.txt';a.click();URL.revokeObjectURL(a.href)}}>Download draft</button></section>}
    {history.length>0 && <details><summary>Session answers ({history.length})</summary>{history.map((h,i)=><article className="source" key={i}><strong>{h.question}</strong><p className="preserve-lines">{h.answer.content.answer}</p><small>Sources: {h.answer.content.cited_record_ids.join(', ')}</small></article>)}<button className="secondary" onClick={()=>{setHistory([]);setAnswer(null);setDraft('')}}>Clear conversation</button></details>}
  </section>
}
function Emails({actorId}:{actorId:number}) {
  const [inbox,setInbox]=useState<Inbox|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(true)
  const [retry,setRetry]=useState(0)
  const [controller]=useState(()=>new AbortController())
  useEffect(()=>()=>controller.abort(),[controller])
  useEffect(()=>{setBusy(true);setError('');void demoRequest<Inbox>('/employee/emails',actorId,controller.signal).then(x=>{if(!controller.signal.aborted){setInbox(x);setBusy(false)}}).catch(e=>{if(!controller.signal.aborted){setError(e.message);setBusy(false)}})},[actorId,controller,retry])
  async function more(){if(!inbox?.next_before)return;setBusy(true);setError('');try{const x=await demoRequest<Inbox>(`/employee/emails?before=${inbox.next_before}`,actorId,controller.signal);if(!controller.signal.aborted)setInbox({...x,messages:[...inbox.messages,...x.messages]})}catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Unable to load email.')}finally{if(!controller.signal.aborted)setBusy(false)}}
  return <section className="evidence-panel"><h3>My synthetic email</h3>{error&&<p className="error" role="alert">{error}<button onClick={()=>setRetry(x=>x+1)}>Retry email</button></p>}{busy&&<p role="status">Loading email…</p>}{inbox&&<><p>{inbox.addresses.join(', ')||'No email address recorded.'}</p><p className="muted">{inbox.scope_note}</p>{!inbox.messages.length&&<p>No email messages are stored for this persona.</p>}{inbox.messages.map(m=><article className="email-message" key={m.email_id}><span className="tag">Thread {m.thread_id} · Message {m.email_id}</span><h4>{m.subject||'(No subject)'}</h4><p><strong>From:</strong> {m.sender_name} · {m.sent_at}</p><p><strong>Recipients:</strong> {m.recipients.map(r=>`${r.name} (${r.recipient_type})`).join(', ')}</p><p className="preserve-lines">{m.body}</p>{m.has_attachments&&<small>Attachment indicated in source; attachment content unavailable.</small>}</article>)}{inbox.next_before&&<button disabled={busy} onClick={()=>void more()}>Load more email</button>}</>}</section>
}
function TeamEngagement({actorId}:{actorId:number}) {
  const [data,setData]=useState<Engagement|null>(null),[error,setError]=useState(''),[group,setGroup]=useState(''),[wave,setWave]=useState(''),[qid,setQid]=useState('Q01'),[retry,setRetry]=useState(0)
  useEffect(()=>{const c=new AbortController();setError('');void demoRequest<Engagement>('/employee/engagement',actorId,c.signal).then(d=>{if(!c.signal.aborted){setData(d);setGroup(String(d.groups[0]?.group_id??''));setWave(String(d.surveys[0]?.survey_id??''))}}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[actorId,retry])
  if(error)return <p className="error">{error}<button onClick={()=>setRetry(x=>x+1)}>Retry engagement</button></p>
  if(!data)return <p role="status">Loading group engagement…</p>
  const result=data.results.find(r=>String(r.group_id)===group&&String(r.survey_id)===wave)
  const sorted=[...(result?.items??[])].filter(r=>r.mean_score!==null).sort((a,b)=>(b.mean_score??0)-(a.mean_score??0))
  return <section><h3>Team engagement (Q12)</h3><p>{data.scope_note}</p>{!data.surveys.length?<p className="empty">No survey waves are loaded in PostgreSQL. Your existing local fixtures have not been imported.</p>:<><div className="q12-controls"><label>Group<select value={group} onChange={e=>setGroup(e.target.value)}>{data.groups.map(g=><option key={g.group_id} value={g.group_id}>{g.group_type}: {g.group_name}</option>)}</select></label><label>Survey wave<select value={wave} onChange={e=>setWave(e.target.value)}>{data.surveys.map(s=><option key={s.survey_id} value={s.survey_id}>{s.reporting_period}</option>)}</select></label></div>
    {!result || result.suppressed?<p className="empty">No reportable results: this group/wave is unavailable or suppressed.</p>:<><div className="metrics"><section className="metric-card"><h4>Strongest items</h4>{sorted.slice(0,3).map(r=><p key={r.question_id}>{Q12_SHORT[r.question_id]} · {r.mean_score?.toFixed(2)}</p>)}</section><section className="metric-card"><h4>Opportunities</h4>{sorted.slice(-2).map(r=><p key={r.question_id}>{Q12_SHORT[r.question_id]} · {r.mean_score?.toFixed(2)}</p>)}</section></div><p className="muted">Where are the 4s? Items with at least 40% of responses at 4: {result.items.filter(r=>r.score_4_count/r.response_count>=.4).map(r=>r.question_id).join(', ')||'None'}. Q01–Q06 form the foundation.</p>
    <div className="q12-bars" aria-label="Q12 mean ratings on a scale of zero to five">{result.items.map(r=><div key={r.question_id}><span>{r.question_id}</span><meter min={0} max={5} value={r.mean_score??0}/><span>{r.mean_score?.toFixed(2)??'Not recorded'} / 5</span></div>)}</div><div className="table-scroll"><table><thead><tr><th>Item</th><th>Statement</th><th>Need</th><th>Mean</th><th>% gave 5</th><th>Synthetic benchmark %</th><th>Counts 1 / 2 / 3 / 4 / 5</th></tr></thead><tbody>{result.items.map(r=><tr key={r.question_id}><td>{r.question_id}</td><td>{r.text}</td><td>{r.engagement_need}</td><td>{value(r.mean_score)}</td><td>{value(r.top_box_pct)}</td><td>{value(r.benchmark_pct)}</td><td>{[r.score_1_count,r.score_2_count,r.score_3_count,r.score_4_count,r.score_5_count].join(' / ')}</td></tr>)}</tbody></table></div><label>Item to focus on<select value={qid} onChange={e=>setQid(e.target.value)}>{result.items.map(r=><option key={r.question_id} value={r.question_id}>{r.question_id} · {Q12_SHORT[r.question_id]}</option>)}</select></label><ul>{Q12_DISCUSS[qid]?.map(q=><li key={q}>{q}</li>)}</ul><Conversation key={`${group}-${wave}-${qid}`} actorId={actorId} subjectId={actorId} engagement prompt={`Help me prepare to discuss ${qid} for group ${group} and survey ${wave}. My thoughts: `}/></>}
    </>}<small>Q12 wording and discussion material © Gallup, Inc. Used for a class project. No Gallup endorsement implied.</small></section>
}
export default function EmployeeWorkspace({actor}:{actor:Current}) {
  const [bundle,setBundle]=useState<Bundle|null>(null),[error,setError]=useState(''),[tab,setTab]=useState(0),[retry,setRetry]=useState(0)
  const id=actor.persona.employee_id
  useEffect(()=>{const c=new AbortController();setBundle(null);setError('');void demoRequest<Bundle>('/employee/record',id,c.signal).then(b=>{if(!c.signal.aborted)setBundle(b)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[id,retry])
  if(error)return <p className="error" role="alert">{error}<button onClick={()=>setRetry(x=>x+1)}>Retry records</button></p>
  if(!bundle)return <p role="status">Loading your own record…</p>
  const records=(category:string)=>bundle.records.filter(r=>r.category===category)
  const reviews=records('reviews').slice().sort((a,b)=>String(a.fields.review_period).localeCompare(String(b.fields.review_period)))
  return <section className="employee-workspace"><header className="employee-header"><div><p className="eyebrow">My workspace</p><h2>Hello, {actor.persona.display_name.split(' ')[0]}.</h2><p>Your work, your growth, and your record.</p></div></header><div className="summary-grid">{['goals','reviews','training','tasks'].map(c=><section className="metric-card" key={c}><p>{label(c)}</p><strong className="summary-count">{bundle.counts[c]??0}</strong></section>)}</div><nav className="tabs" aria-label="My workspace sections">{tabs.map((t,i)=><button className={tab===i?'current':''} key={t} onClick={()=>setTab(i)}>{t}</button>)}</nav><div className="tab-content">
    {tab===0&&<><h3>Goals</h3><Records records={records('goals')}/><h3>Projects and tasks</h3><Records records={records('tasks')}/><h3>Training and development</h3><Records records={records('training')}/><Emails actorId={id}/></>}
    {tab===1&&<><h3>Your review history</h3><p className="muted">Recorded overall ratings, on a fixed 1–5 scale. These are source ratings, not AI evaluations.</p><svg className="review-chart" viewBox="0 0 720 240" role="img" aria-label="Recorded review ratings on a fixed one to five scale">{[1,2,3,4,5].map(n=><g key={n}><line x1={30} x2={700} y1={210-(n-1)*45} y2={210-(n-1)*45} stroke="#d7dfe5"/><text x={10} y={215-(n-1)*45}>{n}</text></g>)}{reviews.map((r,i)=>typeof r.fields.rating_overall==='number'?<g key={r.record_id}><circle cx={50+i*630/Math.max(reviews.length-1,1)} cy={210-(r.fields.rating_overall-1)*45} r={5} fill="#366b94"><title>{r.title}: {r.fields.rating_overall}</title></circle></g>:null)}</svg><Records records={reviews}/><h3>Your self-assessments</h3><Records records={records('self_assessments')}/></>}
    {tab===2&&<TeamEngagement actorId={id}/>}{tab===3&&<Conversation actorId={id} subjectId={id}/>}
    {tab===4&&<><h3>What this tool uses about you</h3><ul>{Object.entries(bundle.counts).map(([c,n])=><li key={c}>{label(c)}: {n} records</li>)}</ul><h3>What it never uses for AI preparation</h3><p>Private manager notes, peer feedback, email content, surveillance, protected characteristics, health/family information, or individual survey responses. Viewing your own synthetic inbox does not add email to AI context.</p><p>Group Q12 results are available only when reportable. Chats and draft edits remain in browser state; durable audit and employee-visible prep activity are not yet implemented.</p><ul>{bundle.gaps.map(g=><li key={g}>{g}</li>)}</ul></>}
    </div></section>
}
