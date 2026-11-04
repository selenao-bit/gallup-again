import { API_BASE_URL } from '../config'

export interface Employee {
  employee_id: number; display_name: string; position_title: string
  department_name: string | null; employment_status: string
}
export interface Persona { employee_id: number; display_name: string; role: 'manager' | 'employee' | 'hr_admin' }
export interface Catalog { demo: true; personas: Persona[]; assistant_mode: 'simulated' | 'openai' | 'azure'; assistant_available?: boolean }
export interface Current { persona: Persona; employee: Employee }
export interface ReportPage { reports: Employee[]; next_after_employee_id: number | null }
export interface Metric { total: number; completed: number; denominator: number; completion_pct: number | null; statuses: Record<string, number>; definition: string }
export interface Source { record_id: string; record_type: string; label: string; status: string; date: string | null; date_label: string }
export interface Dashboard { employee: Employee; team_name: string | null; hire_date: string; role_start_date: string; as_of: string; tasks: Metric; training: Metric; sources: Source[]; data_gaps: string[] }
export interface Answer { answer: string; suggested_approach: string[]; strengths_to_acknowledge: string[]; data_gaps: string[]; sources: Source[]; mode: 'simulated' | 'openai' | 'azure'; scope_note: string }
export const STARTER = 'Summarize recorded task and training progress.'

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message) }
}
export async function demoRequest<T>(path: string, actor: number | null, signal: AbortSignal, question?: string): Promise<T> {
  const deadline = AbortSignal.timeout(question === undefined ? 8_000 : 35_000)
  const combined = AbortSignal.any([signal, deadline])
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      signal: combined, cache: 'no-store', credentials: 'omit', redirect: 'error',
      method: question === undefined ? 'GET' : 'POST',
      headers: { ...(actor !== null ? { 'X-Demo-Employee-Id': String(actor) } : {}), ...(question !== undefined ? { 'Content-Type': 'application/json' } : {}) },
      ...(question !== undefined ? { body: JSON.stringify({ question }) } : {}),
    })
    const data = await response.json()
    if (!response.ok) throw new ApiError(response.status, data.detail?.code || 'unavailable', data.detail?.message || 'The request could not be completed.')
    return data as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(503, 'connection_unavailable', 'The application could not be reached. Check the connection and retry.')
  }
}
