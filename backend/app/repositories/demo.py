"""Verified PostgreSQL projections. Every subject read repeats the current edge predicate."""
from sqlalchemy import bindparam, text
from ..database import Database
from ..services.access import ACTOR_STATUSES, TARGET_STATUSES, Actor

PROFILE = '''SELECT e.employee_id, e.employee_fname || ' ' || e.employee_lname AS display_name,
 p.position_title, d.department_name, e.employment_status
 FROM public.employees e JOIN public.positions p ON p.position_id=e.position_id
 LEFT JOIN public.departments d ON d.department_id=e.department_id'''
# Reused in every data query, never a caller/model-selected scope.
SCOPE = '''e.employee_id=:subject_id AND e.supervisor_id=:actor_id AND e.employee_id<>:actor_id
 AND e.employment_status IN :target_statuses AND EXISTS
 (SELECT 1 FROM public.employees a WHERE a.employee_id=:actor_id AND a.employment_status IN :actor_statuses)'''

def scoped(statement):
    return text(statement).bindparams(bindparam('target_statuses', expanding=True), bindparam('actor_statuses', expanding=True))

def scope_params(actor: Actor, subject_id: int):
    return dict(actor_id=actor.employee_id, subject_id=subject_id,
                target_statuses=TARGET_STATUSES, actor_statuses=ACTOR_STATUSES)

class DemoRepository:
    def __init__(self, database: Database):
        self.database = database

    def employee(self, employee_id: int):
        with self.database.read() as c:
            return c.execute(text(PROFILE + ' WHERE e.employee_id=:id AND e.employment_status IN :statuses')
                .bindparams(bindparam('statuses', expanding=True)), {'id': employee_id, 'statuses': ACTOR_STATUSES}).mappings().first()

    def reports(self, actor: Actor, limit: int, after: int | None):
        sql = PROFILE + ''' WHERE e.supervisor_id=:actor_id AND e.employee_id<>:actor_id
        AND e.employment_status IN :statuses AND (CAST(:after AS INTEGER) IS NULL OR e.employee_id>:after)
        ORDER BY e.employee_id LIMIT :limit'''
        with self.database.read() as c:
            return c.execute(text(sql).bindparams(bindparam('statuses', expanding=True)),
                dict(actor_id=actor.employee_id, statuses=TARGET_STATUSES, after=after, limit=limit+1)).mappings().all()

    def overview(self, actor: Actor, subject_id: int):
        params = scope_params(actor, subject_id)
        with self.database.read() as c:
            profile = c.execute(scoped(PROFILE + ' WHERE ' + SCOPE), params).mappings().first()
            if profile is None:
                return None
            context = c.execute(scoped('''SELECT t.team_name, e.hire_date::date AS hire_date,
                e.role_start_date::date AS role_start_date FROM public.employees e
                LEFT JOIN public.teams t ON t.team_id=e.team_id WHERE ''' + SCOPE), params).mappings().first()
            if context is None:
                return None
            results = {}
            # Identifiers below are hardcoded, never interpolated from request/model input.
            for table, key, label, status, ordering, event in (
                ('project_tasks', 'task_id', 'title', 'task_status', 'created_date', 'complete_date'),
                ('employee_training', 'training_id', 'program_name', 'completion_status', 'assigned_date', 'completion_date'),
            ):
                predicate = f' FROM public.{table} r JOIN public.employees e ON e.employee_id=r.employee_id WHERE {SCOPE}'
                counts = c.execute(scoped(f'SELECT r.{status} AS status, count(*) AS count' + predicate + f' GROUP BY r.{status}'), params).mappings().all()
                rows = c.execute(scoped(f'''SELECT r.{key} AS id, left(r.{label}, 180) AS label,
                    r.{status} AS status, r.{event}::date AS date''' + predicate +
                    f' ORDER BY r.{ordering} DESC, r.{key} DESC LIMIT 8'), params).mappings().all()
                results[table] = (counts, rows)
            return dict(profile=profile, context=context, results=results)
