import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import { STARTER } from './api/demo'

const employee = (id = 7) => ({ employee_id: id, display_name: `Report ${id}`, position_title: 'Analyst', department_name: null, employment_status: 'Active' })
const metric = { total: 2, completed: 1, denominator: 2, completion_pct: 50, statuses: { Complete: 1, 'In Progress': 1 }, definition: 'Record count definition' }
const source = { record_id: 'project_tasks:4', record_type: 'project_tasks', label: 'Recorded task', status: 'Complete', date: null, date_label: 'Completion date' }
const dashboard = (id = 7) => ({ employee: employee(id), team_name: null, hire_date: '2020-01-01', role_start_date: '2021-01-01', as_of: '2026-10-28', tasks: metric, training: metric, sources: [source], data_gaps: ['No review-period comparison.'] })
function setup() {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async (url: string, options: RequestInit) => {
    let body: unknown
    if (url.endsWith('/health')) body = { status: 'ok' }
    else if (url.endsWith('/demo/personas')) body = { demo: true, assistant_mode: 'simulated', personas: [{ employee_id: 60, display_name: 'Manager persona', role: 'manager' }, { employee_id: 1, display_name: 'Employee persona', role: 'employee' }] }
    else if (url.endsWith('/demo/me')) {
      const id = (options.headers as Record<string, string>)['X-Demo-Employee-Id']
      body = { persona: { employee_id: Number(id), display_name: id === '60' ? 'Manager persona' : 'Employee persona', role: id === '60' ? 'manager' : 'employee' }, employee: employee(Number(id)) }
    } else if (url.endsWith('/manager/reports')) body = { reports: [employee(7), employee(8)], next_after_employee_id: null }
    else if (url.endsWith('/record')) body = { employee: employee(), records: [], counts: {goals:0,reviews:0,training:0,tasks:0,self_assessments:0}, gaps:[] }
    else if (url.endsWith('/employee/emails')) body = {addresses:[],messages:[],next_before:null,scope_note:'Only messages this persona sent or received.'}
    else if (url.endsWith('/dashboard')) body = dashboard(url.includes('/8/') ? 8 : 7)
    else if (url.endsWith('/chat')) body = { answer: 'Recorded progress summary.', suggested_approach: ['Ask about support.'], strengths_to_acknowledge: [], data_gaps: [], sources: [source], mode: 'simulated', scope_note: 'Preparation support only.' }
    else throw new Error('Unexpected request')
    return new Response(JSON.stringify(body), { status: 200 })
  }))
  render(<App />)
}

describe('manager demo workflow', () => {
  it('selects persona and report, renders evidence and a labeled answer, clears on subject/persona change', async () => {
    setup()
    await screen.findByRole('option', { name: /Manager persona/ })
    fireEvent.change(screen.getByLabelText('Demo persona'), { target: { value: '60' } })
    fireEvent.click(await screen.findByRole('button', { name: 'My direct reports' }))
    fireEvent.click(await screen.findByRole('button', { name: /Report 7/ }))
    await screen.findByRole('heading', { name: 'Report 7' })
    expect(screen.getByText('project_tasks:4')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: /Review preparation/ }))
    fireEvent.click(screen.getByText('Existing task and training summary'))
    fireEvent.click(screen.getByRole('button', { name: 'Prepare answer ↗' }))
    expect(await screen.findByText('Recorded progress summary.')).toBeVisible()
    expect(screen.getByText('Simulated answer · real database evidence')).toBeVisible()
    expect(vi.mocked(fetch).mock.calls.find(([path]) => String(path).endsWith('/chat'))?.[1]?.body).toBe(JSON.stringify({ question: STARTER }))
    fireEvent.click(screen.getByRole('button', { name: /Report 8/ }))
    await screen.findByRole('heading', { name: 'Report 8' })
    expect(screen.queryByText('Recorded progress summary.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Report 8/ }))
    expect(screen.getByRole('heading', { name: 'Report 8' })).toBeVisible()
    fireEvent.change(screen.getByLabelText('Demo persona'), { target: { value: '1' } })
    expect(screen.queryByRole('heading', { name: 'Report 8' })).not.toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Hello, Employee.' })).toBeVisible()
    expect(screen.queryByRole('heading', { name: 'Direct reports' })).not.toBeInTheDocument()
  })
  it('clears stale identity data when selection is cleared', async () => {
    setup()
    await screen.findByRole('option', { name: /Manager persona/ })
    fireEvent.change(screen.getByLabelText('Demo persona'), { target: { value: '60' } })
    fireEvent.click(await screen.findByRole('button', { name: 'My direct reports' }))
    await screen.findByRole('heading', { name: 'Direct reports' })
    fireEvent.click(screen.getByRole('button', { name: 'Clear selection' }))
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Direct reports' })).not.toBeInTheDocument())
    expect(localStorage.getItem('demo.employee_id')).toBeNull()
  })
})
