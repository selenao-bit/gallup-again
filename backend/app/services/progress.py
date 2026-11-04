"""Shared factual completion rates; unavailable denominators are never zero scores."""
from collections.abc import Mapping
from typing import Literal
from ..demo_models import Metric


def completion_metric(statuses: Mapping[str, int], category: Literal['tasks','training']) -> Metric:
    task = category == 'tasks'
    excluded, done = ('Cancelled','Complete') if task else ('Withdrawn','Completed')
    total = sum(statuses.values())
    denominator = total - statuses.get(excluded,0)
    completed = statuses.get(done,0)
    definition = ('Complete / all non-Cancelled assigned tasks; Suspended included.' if task else
                  'Completed / all non-Withdrawn training assignments; Expired included.')
    return Metric(total=total,completed=completed,denominator=denominator,
                  completion_pct=round(100*completed/denominator,1) if denominator else None,
                  statuses=dict(statuses),definition=definition)
