"""Read-only, explicit PostgreSQL projections; never reads private manager notes."""
from datetime import date, datetime
from sqlalchemy import text
from ..demo_models import Persona, EmployeeSummary
from ..workspace_models import Record, RecordBundle
from ..services.access import Actor, DemoError
from .demo import PROFILE, TARGET_STATUSES, scoped, scope_params, SCOPE

# All identifiers/projections are fixed in code, not model or request arguments.
PROJECTIONS = {
    'goals': ('employee_goals', 'goal_id', 'goal_description', 'complete_status', 'start_date',
              'goal_id, goal_description, start_date, end_date, complete_status, complete_desc'),
    'tasks': ('project_tasks', 'task_id', 'title', 'task_status', 'created_date',
              'task_id, title, description, created_date, due_date, complete_date, task_status, revision_count, project_id'),
    'training': ('employee_training', 'training_id', 'program_name', 'completion_status', 'assigned_date',
                 'training_id, program_name, program_category, training_type, provider, is_mandatory, assigned_date, start_date, due_date, completion_date, completion_status, estimated_hours, actual_hours, assessment_score, certification_awarded, certification_expiry, employee_feedback'),
    'reviews': ('performance_reviews', 'review_id', 'review_period', None, 'review_id',
                'review_id, review_period, task_completion_pct, goal_completion_pct, rating_overall, comments_overall, rating_work_quality, comments_work_quality, rating_time_mgmt, comments_time_mgmt, rating_comm, comments_comm, rating_adapt, comments_adapt, development_areas'),
    'self_assessments': ('self_assessments', 'assessment_id', 'review_period', None, 'submission_date',
                         'assessment_id, review_period, major_accomplishments, challenges_encountered, goal_reflections, skills_developed, areas_for_improvement, career_interests, requested_support, submission_date'),
}

def scalar(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value

class WorkspaceRepository:
    def __init__(self, database):
        self.database = database

    def personas(self):
        with self.database.read() as c:
            return c.execute(text(PROFILE.replace(' FROM public.employees', ", EXISTS (SELECT 1 FROM public.employees r WHERE r.supervisor_id=e.employee_id AND r.employee_id<>e.employee_id AND r.employment_status IN ('Active','Leave')) AS has_reports FROM public.employees", 1) + " WHERE e.employment_status='Active' ORDER BY e.employee_id")).mappings().all()

    def persona(self, employee_id):
        with self.database.read() as c:
            return c.execute(text(PROFILE + ''' WHERE e.employee_id=:id AND e.employment_status='Active' '''), {'id':employee_id}).mappings().first()

    def has_reports(self, employee_id):
        with self.database.read() as c:
            return c.execute(text('''SELECT EXISTS (SELECT 1 FROM public.employees
                WHERE supervisor_id=:id AND employee_id<>:id AND employment_status IN ('Active','Leave'))'''), {'id':employee_id}).scalar_one()

    def bundle(self, actor: Actor, subject_id: int):
        if not -2147483648 <= subject_id <= 2147483647:
            raise DemoError(404, 'employee_unavailable', 'Employee unavailable in the current scope.')
        own = subject_id == actor.employee_id
        if not own and actor.role != 'manager':
            raise DemoError(404, 'employee_unavailable', 'Employee unavailable in the current scope.')
        predicate = "e.employee_id=:subject_id AND e.employment_status='Active'" if own else SCOPE
        params = scope_params(actor, subject_id)
        with self.database.read() as c:
            query = text(PROFILE+' WHERE '+predicate) if own else scoped(PROFILE+' WHERE '+predicate)
            profile = c.execute(query, params).mappings().first()
            if not profile:
                raise DemoError(404, 'employee_unavailable', 'Employee unavailable in the current scope.')
            records, counts, gaps = [], {}, []
            for category, (table, key, title, status, ordering, columns) in PROJECTIONS.items():
                if not own and category in ('reviews', 'self_assessments'):
                    continue  # Additional manager visibility has not been approved.
                source = f' FROM public.{table} r JOIN public.employees e ON e.employee_id=r.employee_id WHERE {predicate}'
                prepare = text if own else scoped
                counts[category] = c.execute(prepare('SELECT count(*)'+source),params).scalar_one()
                projection = ', '.join('r.'+col.strip() for col in columns.split(','))
                if category == 'tasks':
                    projection += ', (SELECT p.project_name FROM public.projects p WHERE p.project_id=r.project_id) AS project_name'
                rows=c.execute(prepare('SELECT '+projection+source+f' ORDER BY r.{ordering} DESC NULLS LAST, r.{key} DESC LIMIT 200'),params).mappings().all()
                for row in rows:
                    fields={k:scalar(v) for k,v in row.items()}
                    value=row[ordering]
                    record_date = scalar(value) if isinstance(value,(date,datetime)) else None
                    records.append(Record(record_id=f'{table}:{row[key]}',category=category,title=str(row[title]),
                        status=row[status] if status else None,date=record_date,fields=fields))
                if counts[category] > len(rows): gaps.append(f'{category}: showing the latest 200 of {counts[category]} records.')
            if not own: gaps.append('Private notes, peer feedback, reviews, self-assessments and email are excluded from manager preparation.')
            gaps.append('Goals have recorded statuses and dates; an end date is not evidence of actual completion time.')
            return RecordBundle(employee=EmployeeSummary(**profile),records=records,counts=counts,gaps=gaps)

    def emails(self, actor: Actor, before: int | None):
        # Enforce message-level participation, including when messages share a thread.
        with self.database.read() as c:
            addresses = c.execute(text('SELECT email_address FROM public.email_accounts WHERE employee_id=:id ORDER BY email_address'), {'id':actor.employee_id}).scalars().all()
            rows=c.execute(text('''SELECT m.email_id,m.thread_id,m.sender_id,m.sent_at,m.subject,m.body,m.reply_to_id,
                m.has_attachments, s.employee_fname || ' ' || s.employee_lname AS sender_name
                FROM public.email_records m JOIN public.employees s ON s.employee_id=m.sender_id
                WHERE (m.sender_id=:id OR EXISTS (SELECT 1 FROM public.email_recipients r
                    WHERE r.email_id=m.email_id AND r.recipient_id=:id))
                AND (CAST(:before AS INTEGER) IS NULL OR m.email_id<:before)
                ORDER BY m.email_id DESC LIMIT 51'''),{'id':actor.employee_id,'before':before}).mappings().all()
            messages=[]
            for row in rows[:50]:
                recipients=c.execute(text('''SELECT r.recipient_id,r.recipient_type,e.employee_fname || ' ' || e.employee_lname AS name
                    FROM public.email_recipients r JOIN public.employees e ON e.employee_id=r.recipient_id
                    WHERE r.email_id=:message AND (r.recipient_type<>'bcc' OR :id=:sender OR r.recipient_id=:id)
                    ORDER BY r.recipient_type,r.recipient_id'''),{'message':row['email_id'],'id':actor.employee_id,'sender':row['sender_id']}).mappings().all()
                messages.append({**{k:scalar(v) for k,v in row.items()}, 'recipients':[dict(r) for r in recipients]})
            return {'addresses':addresses,'messages':messages,'next_before':rows[49]['email_id'] if len(rows)>50 else None,
                    'scope_note':'Only messages this persona sent or received. Other messages in the same thread remain hidden. Attachments are not stored here.'}

    def engagement(self, actor):
        with self.database.read() as c:
            groups=c.execute(text('''SELECT g.group_id,g.group_name,g.group_type FROM public.q12_groups g
                JOIN public.employees e ON e.employee_id=:id AND e.employment_status='Active'
                WHERE g.group_type='Company' OR (g.group_type='Team' AND g.team_id=e.team_id)
                   OR (g.group_type='Department' AND g.department_id=e.department_id)
                ORDER BY g.group_id'''),{'id':actor.employee_id}).mappings().all()
            surveys=c.execute(text('SELECT survey_id,reporting_period FROM public.q12_surveys ORDER BY start_date DESC')).mappings().all()
            results=[]
            for group in groups:
                for survey in surveys:
                    params={'group':group['group_id'],'survey':survey['survey_id']}
                    # Suppress the whole group/wave before returning any value/count.
                    hidden=c.execute(text('''SELECT count(*)=0 OR bool_or(is_suppressed OR response_count IS NULL OR response_count<5)
                        FROM public.q12_results WHERE group_id=:group AND survey_id=:survey AND question_id<>'Q00' '''),params).scalar_one()
                    rows=[] if hidden else c.execute(text('''SELECT r.question_id,q.text,q.element,q.engagement_need,r.mean_score,r.top_box_pct,r.benchmark_pct,
                        r.response_count,r.score_1_count,r.score_2_count,r.score_3_count,r.score_4_count,r.score_5_count
                        FROM public.q12_results r JOIN public.q12_questions q ON q.id=r.question_id
                        WHERE r.group_id=:group AND r.survey_id=:survey AND r.question_id<>'Q00' ORDER BY r.question_id'''),params).mappings().all()
                    results.append({'group_id':group['group_id'],'survey_id':survey['survey_id'],'suppressed':bool(hidden),'items':[dict(r) for r in rows]})
            return {'groups':[dict(g) for g in groups],'surveys':[dict(s) for s in surveys],'results':results,
                    'scope_note':'Synthetic group engagement context, not employee performance. Groups with fewer than five responses or a suppression flag are hidden. Benchmarks are synthetic.'}
