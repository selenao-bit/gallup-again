import { fireEvent, render, screen } from '@testing-library/react'
import { StrictMode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import EmployeeWorkspace, { Conversation } from './EmployeeWorkspace'
const actor={persona:{employee_id:2,display_name:'Alex Employee',role:'employee' as const},employee:{employee_id:2,display_name:'Alex Employee',position_title:'Analyst',department_name:null,employment_status:'Active'}}
function setup(){
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
    const body=url.endsWith('/record')?{employee:actor.employee,records:[{record_id:'employee_goals:2',category:'goals',title:'Own goal',status:'In Progress',date:null,fields:{goal_description:'Own goal'}}],counts:{goals:1,tasks:0,training:0,reviews:0,self_assessments:0},gaps:[]}:
      url.endsWith('/emails')?{addresses:['alex@example.test'],messages:[],next_before:null,scope_note:'Participation-only access.'}:
      {groups:[],surveys:[],results:[],scope_note:'Synthetic group engagement.'}
    return new Response(JSON.stringify(body),{status:200})
  }))
  render(<EmployeeWorkspace actor={actor}/> )
}
describe('employee integration',()=>{
  it('completes an Ask my record request after StrictMode lifecycle checks',async()=>{
    vi.stubGlobal('fetch',vi.fn(async(_url:string,options?:RequestInit)=>{
      options?.signal?.throwIfAborted()
      return new Response(JSON.stringify({content:{answer:'Recorded training answer.',discussion_questions:[],data_gaps:[],cited_record_ids:['employee_training:2']},sources:[]}),{status:200})
    }))
    render(<StrictMode><Conversation actorId={2} subjectId={2}/></StrictMode>)
    fireEvent.change(screen.getByRole('textbox'),{target:{value:'What training have I completed?'}})
    fireEvent.click(screen.getByRole('button',{name:'Prepare with AI'}))
    expect((await screen.findAllByText('Recorded training answer.'))[0]).toBeVisible()
    expect(screen.getByRole('button',{name:'Prepare with AI'})).toBeEnabled()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
  it('preserves five sections and shows an honest empty inbox',async()=>{
    setup()
    expect((await screen.findAllByText('Own goal'))[0]).toBeVisible()
    expect(screen.getByRole('button',{name:'My reviews'})).toBeVisible()
    expect(screen.queryByRole('button',{name:'My voice'})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:'Prepare my conversation'})).not.toBeInTheDocument()
    expect(await screen.findByText('alex@example.test')).toBeVisible()
    expect(screen.getByText('No email messages are stored for this persona.')).toBeVisible()
    expect(vi.mocked(fetch).mock.calls.find(([u])=>String(u).endsWith('/record'))?.[1]).toEqual(expect.objectContaining({headers:{'X-Demo-Employee-Id':'2'}}))
  })
  it('reports missing Q12 waves without fabricating results',async()=>{
    setup();await screen.findAllByText('Own goal')
    fireEvent.click(screen.getByRole('button',{name:'Team engagement (Q12)'}))
    expect(await screen.findByText(/No survey waves are loaded/)).toBeVisible()
    expect(screen.queryByText('Strongest items')).not.toBeInTheDocument()
  })
  it('shows an unavailable AI error and never substitutes an answer',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({detail:{code:'assistant_unavailable',message:'Live AI is not configured.'}}),{status:503})))
    render(<StrictMode><Conversation actorId={2} subjectId={2}/></StrictMode>)
    fireEvent.change(screen.getByRole('textbox'),{target:{value:'What goals do I have?'}})
    fireEvent.click(screen.getByRole('button',{name:'Prepare with AI'}))
    expect(await screen.findByRole('alert')).toHaveTextContent('Live AI is not configured.')
    expect(screen.getByRole('button',{name:'Prepare with AI'})).toBeEnabled()
    expect(screen.queryByText('AI answer · source IDs validated')).not.toBeInTheDocument()
  })
  it('cancels the active chat request when leaving the section',()=>{
    let signal:AbortSignal|null|undefined
    vi.stubGlobal('fetch',vi.fn((_url:string,options?:RequestInit)=>{
      signal=options?.signal
      return new Promise<Response>(()=>{})
    }))
    const view=render(<StrictMode><Conversation actorId={2} subjectId={2}/></StrictMode>)
    fireEvent.change(screen.getByRole('textbox'),{target:{value:'What goals do I have?'}})
    fireEvent.click(screen.getByRole('button',{name:'Prepare with AI'}))
    expect(signal?.aborted).toBe(false)
    view.unmount()
    expect(signal?.aborted).toBe(true)
  })
})

describe('task completion display',()=>{
  const base={total:4,denominator:4,completed:3,completion_pct:75,statuses:{Complete:3,'In Progress':1},definition:'Complete / all non-Cancelled assigned tasks; Suspended included.'}
  it('shows a numeric completion rate from server metrics',async()=>{
    const {TaskProgress}=await import('./EmployeeWorkspace')
    render(<TaskProgress metric={base}/> )
    expect(screen.getByText('75%')).toBeVisible()
    expect(screen.getByRole('meter',{name:'Task completion rate'})).toHaveAttribute('value','75')
  })
  it('distinguishes no assignments from a real zero',async()=>{
    const {TaskProgress}=await import('./EmployeeWorkspace')
    const view=render(<TaskProgress metric={{...base,total:0,denominator:0,completed:0,completion_pct:null,statuses:{}}}/> )
    expect(screen.getByText('No assigned tasks')).toBeVisible()
    expect(screen.queryByText('0%')).not.toBeInTheDocument()
    view.rerender(<TaskProgress metric={{...base,completed:0,completion_pct:0}}/> )
    expect(screen.getByText('0%')).toBeVisible()
  })
  it('explains cancelled-only denominators',async()=>{
    const {TaskProgress}=await import('./EmployeeWorkspace')
    render(<TaskProgress metric={{...base,total:2,denominator:0,completed:0,completion_pct:null,statuses:{Cancelled:2}}}/> )
    expect(screen.getByText('No eligible tasks')).toBeVisible()
  })
})

describe('populated Q12 display',()=>{
  it('shows loaded scores and clears them when switching to a suppressed wave',async()=>{
    const item={question_id:'Q01',text:'Clear work expectations',element:'Basic Needs',engagement_need:'Focus me.',mean_score:3.7,top_box_pct:20,benchmark_pct:58,response_count:10,score_1_count:0,score_2_count:1,score_3_count:3,score_4_count:4,score_5_count:2}
    vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
      let body:unknown
      if(url.endsWith('/record')) body={employee:actor.employee,records:[],counts:{goals:0,tasks:0,training:0,reviews:0},gaps:[]}
      else if(url.endsWith('/emails')) body={addresses:[],messages:[],next_before:null,scope_note:'Participation-only.'}
      else body={groups:[{group_id:3,group_name:'Demo team',group_type:'Team'}],surveys:[{survey_id:2,reporting_period:'2026-H1'},{survey_id:1,reporting_period:'2025-H2'}],results:[{group_id:3,survey_id:2,suppressed:false,items:[item]},{group_id:3,survey_id:1,suppressed:true,items:[]}],scope_note:'Synthetic group context.'}
      return new Response(JSON.stringify(body),{status:200})
    }))
    render(<EmployeeWorkspace actor={actor}/>)
    fireEvent.click(await screen.findByRole('button',{name:'Team engagement (Q12)'}))
    expect(await screen.findByText('Strongest items')).toBeVisible()
    expect(screen.getByText('3.70 / 5')).toBeVisible()
    fireEvent.change(screen.getByLabelText('Survey wave'),{target:{value:'1'}})
    expect(screen.getByText(/No reportable results/)).toBeVisible()
    expect(screen.queryByText('3.70 / 5')).not.toBeInTheDocument()
  })
})
