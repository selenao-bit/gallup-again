"""Completion-rate definitions shared by employee and manager views."""
from app.services.progress import completion_metric


def test_real_zero_differs_from_no_assignments():
    none=completion_metric({},'tasks')
    zero=completion_metric({'In Progress':3},'tasks')
    assert none.completion_pct is None and none.total==0
    assert zero.completion_pct==0 and zero.denominator==3


def test_cancelled_tasks_are_excluded_and_suspended_included():
    metric=completion_metric({'Complete':3,'Cancelled':2,'Suspended':1},'tasks')
    assert metric.total==6 and metric.denominator==4 and metric.completion_pct==75
    assert completion_metric({'Cancelled':2},'tasks').completion_pct is None


def test_training_uses_its_own_statuses():
    metric=completion_metric({'Completed':2,'Withdrawn':5,'Expired':2},'training')
    assert metric.total==9 and metric.denominator==4 and metric.completion_pct==50
