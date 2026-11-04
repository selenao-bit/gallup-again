"""Contracts shared by employee record viewing and bounded AI retrieval."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .demo_models import EmployeeSummary, Metric

class Record(BaseModel):
    record_id: str
    category: str
    title: str
    status: str | None = None
    date: str | None = None
    fields: dict[str, str | float | int | bool | None]

class RecordBundle(BaseModel):
    employee: EmployeeSummary
    records: list[Record]
    counts: dict[str, int]
    gaps: list[str]
    task_progress: Metric | None = None

class WorkspaceQuestion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=2000)

class WorkspaceAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: str
    discussion_questions: list[str]
    data_gaps: list[str]
    cited_record_ids: list[str]

class AnswerResult(BaseModel):
    content: WorkspaceAnswer
    sources: list[Record]
    mode: Literal['openai','azure'] = 'openai'
