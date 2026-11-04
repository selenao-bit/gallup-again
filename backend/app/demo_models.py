"""Small explicit transport/domain contracts for the synthetic demonstration."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Role = Literal['employee', 'manager', 'hr_admin']

class EmployeeSummary(BaseModel):
    employee_id: int
    display_name: str
    position_title: str
    department_name: str | None
    employment_status: Literal['Active', 'Leave', 'Terminated']

class Persona(BaseModel):
    employee_id: int
    display_name: str
    role: Role

class PersonaList(BaseModel):
    demo: Literal[True] = True
    personas: list[Persona]
    assistant_available: bool = False
    assistant_mode: Literal['simulated', 'openai', 'azure']

class CurrentPersona(BaseModel):
    demo: Literal[True] = True
    persona: Persona
    employee: EmployeeSummary

class ReportPage(BaseModel):
    demo: Literal[True] = True
    reports: list[EmployeeSummary]
    next_after_employee_id: int | None

class Metric(BaseModel):
    total: int
    completed: int
    denominator: int
    completion_pct: float | None
    statuses: dict[str, int]
    definition: str

class Source(BaseModel):
    record_id: str
    record_type: Literal['project_tasks', 'employee_training']
    label: str
    status: str
    date: date | None
    date_label: str

class Dashboard(BaseModel):
    demo: Literal[True] = True
    employee: EmployeeSummary
    team_name: str | None
    hire_date: date
    role_start_date: date
    as_of: date
    tasks: Metric
    training: Metric
    sources: list[Source]
    data_gaps: list[str]

QUESTIONS = (
    'Summarize recorded task and training progress.',
    'What task and training progress should I discuss?',
)

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=500)

class AnswerContent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: str
    suggested_approach: list[str]
    strengths_to_acknowledge: list[str]
    data_gaps: list[str]
    cited_record_ids: list[str]

class ChatAnswer(AnswerContent):
    mode: Literal['simulated', 'openai', 'azure']
    sources: list[Source]
    scope_note: str
