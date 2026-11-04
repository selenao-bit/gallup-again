import { fireEvent, render, screen } from '@testing-library/react'
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
    render(<Conversation actorId={2} subjectId={2}/>)
    fireEvent.change(screen.getByRole('textbox'),{target:{value:'What goals do I have?'}})
    fireEvent.click(screen.getByRole('button',{name:'Prepare with AI'}))
    expect(await screen.findByRole('alert')).toHaveTextContent('Live AI is not configured.')
    expect(screen.queryByText('AI answer · source IDs validated')).not.toBeInTheDocument()
  })
})
