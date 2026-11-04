"""Demo identity resolution and shared, bounded employee context."""
from ..demo_models import PersonaList, Persona, CurrentPersona, EmployeeSummary
from .access import Actor, DemoError

class WorkspaceService:
    def __init__(self, repository, settings):
        self.repository, self.settings = repository, settings

    def personas(self):
        rows=self.repository.personas()
        return PersonaList(personas=[Persona(employee_id=r['employee_id'], display_name=r['display_name'],
            role='manager' if r['has_reports'] else 'employee') for r in rows], assistant_mode=self.settings.assistant_mode)

    def resolve(self, employee_id):
        row=self.repository.persona(employee_id)
        if row is None:
            raise DemoError(401,'demo_selection_invalid','Select an available synthetic persona.')
        role='manager' if self.repository.has_reports(employee_id) else 'employee'
        return Actor(employee_id,role), CurrentPersona(persona=Persona(employee_id=employee_id,display_name=row['display_name'],role=role),employee=EmployeeSummary(**row))
