"""Shared factual calculations used by the API and the pinned assistant tool."""
from datetime import date
from ..config import Settings
from ..demo_models import CurrentPersona, Dashboard, EmployeeSummary, Metric, Persona, PersonaList, ReportPage, Source
from ..repositories.demo import DemoRepository
from .access import Actor, DemoError, PERSONAS, require_manager, unavailable
from .progress import completion_metric

class DemoService:
    def __init__(self, repository: DemoRepository, settings: Settings):
        self.repository, self.settings = repository, settings

    def personas(self) -> PersonaList:
        values = []
        for employee_id, role in PERSONAS.items():
            row = self.repository.employee(employee_id)
            if row:
                values.append(Persona(employee_id=employee_id, display_name=row['display_name'], role=role))
        return PersonaList(personas=values, assistant_mode=self.settings.assistant_mode)

    def resolve(self, employee_id: int) -> tuple[Actor, CurrentPersona]:
        role = PERSONAS.get(employee_id)
        row = self.repository.employee(employee_id) if role else None
        if row is None:
            raise DemoError(401, 'demo_selection_invalid', 'Select an available demo persona.')
        actor = Actor(employee_id, role)
        return actor, CurrentPersona(persona=Persona(employee_id=employee_id, display_name=row['display_name'], role=role), employee=EmployeeSummary(**row))

    def reports(self, actor: Actor, limit: int, after: int | None) -> ReportPage:
        require_manager(actor)
        rows = self.repository.reports(actor, limit, after)
        return ReportPage(reports=[EmployeeSummary(**r) for r in rows[:limit]],
                          next_after_employee_id=rows[limit-1]['employee_id'] if len(rows)>limit else None)

    def overview(self, actor: Actor, subject_id: int) -> Dashboard:
        require_manager(actor)
        if not -2147483648 <= subject_id <= 2147483647:
            raise unavailable()
        result = self.repository.overview(actor, subject_id)
        if result is None:
            raise unavailable()
        metrics, sources, gaps = {}, [], []
        for table, (counts, rows) in result['results'].items():
            is_task = table == 'project_tasks'
            statuses = {r['status']: r['count'] for r in counts}
            key = 'tasks' if is_task else 'training'
            metrics[key] = completion_metric(statuses, key)
            total = metrics[key].total
            for r in rows:
                sources.append(Source(record_id=f"{table}:{r['id']}", record_type=table,
                    label=r['label'], status=r['status'], date=r['date'], date_label='Completion date'))
            if total == 0:
                gaps.append(f'No {key} records are available for this employee.')
            if total > len(rows):
                gaps.append(f'{key.title()} evidence shows the 8 most recently assigned/created records; counts cover all {total} records.')
        gaps += ['All-time records; no review-period comparison or employee rating is calculated.',
                 'Feedback, reviews, notes, email and engagement data are excluded from this demonstration.']
        return Dashboard(employee=EmployeeSummary(**result['profile']), **result['context'],
            as_of=date.today(), sources=sources, data_gaps=gaps, **metrics)
