"""Focused boundary checks independent of private PostgreSQL configuration."""
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.demo_models import QUESTIONS, EmployeeSummary, Metric, Dashboard, Source
from app.services.access import Actor, DemoError
from app.services.demo import DemoService
from app.ai.assistant import Assistant
from app.database import DatabaseUnavailable

URL = 'postgresql://demo:demo@localhost/demo'
EMPLOYEE = dict(employee_id=60, display_name='Synthetic Manager', position_title='Test', department_name=None, employment_status='Active')

def fixture_app(enabled=True):
    app = create_app(Settings(database_url=URL, demo_identity_enabled=enabled))
    repository = Mock()
    repository.employee.side_effect = lambda value: dict(EMPLOYEE, employee_id=value) if value in {1, 2, 60} else None
    app.state.demo_service.repository = repository
    workspace_repository = Mock()
    workspace_repository.persona.side_effect = repository.employee.side_effect
    workspace_repository.has_reports.side_effect = lambda value: value == 60
    app.state.workspace_service.repository = workspace_repository
    return app, repository

def test_disabled_does_not_retrieve():
    app, repo = fixture_app(False)
    with TestClient(app) as client:
        for path in ['/demo/personas','/demo/me','/manager/reports','/manager/reports/3/dashboard']:
            assert client.get(path).status_code == 404
    repo.employee.assert_not_called()

@pytest.mark.parametrize('headers,status', [({},401), ({'X-Demo-Employee-Id':'nonsense'},422), ({'X-Demo-Employee-Id':'1,60'},422), ({'X-Demo-Employee-Id':'2147483648'},422), ({'X-Demo-Employee-Id':'3'},401)])
def test_header_boundaries(headers,status):
    app, _ = fixture_app()
    with TestClient(app) as client:
        assert client.get('/demo/me',headers=headers).status_code == status

@pytest.mark.parametrize('persona',[1,2])
def test_non_manager_denied(persona):
    app, repo = fixture_app()
    with TestClient(app) as client:
        for path in ['/manager/reports', '/manager/reports/4/dashboard']:
            assert client.get(path,headers={'X-Demo-Employee-Id':str(persona)}).status_code == 403
    repo.reports.assert_not_called()
    repo.overview.assert_not_called()

def test_scoping_pagination_and_safe_errors():
    app, repo = fixture_app()
    repo.reports.return_value = [dict(EMPLOYEE,employee_id=7),dict(EMPLOYEE,employee_id=9)]
    repo.overview.return_value = None
    with TestClient(app) as client:
        headers = {'X-Demo-Employee-Id':'60'}
        response = client.get('/manager/reports?limit=1', headers=headers)
        assert response.json()['next_after_employee_id'] == 7
        assert response.headers['cache-control'] == 'no-store'
        assert repo.reports.call_args.args == (Actor(60,'manager'),1,None)
        assert client.get('/manager/reports?manager_id=1',headers=headers).status_code == 422
        assert client.get('/manager/reports/9/dashboard',headers=headers).status_code == 404
        assert client.post('/manager/reports/9/chat',headers=headers,json={'question':QUESTIONS[0],'employee_id':1}).status_code == 422
        app.state.workspace_service.repository.persona.side_effect = DatabaseUnavailable('secret driver details')
        response = client.get('/demo/me',headers=headers)
        assert response.status_code == 503
        assert 'secret' not in response.text

def test_summary_zero_denominator_and_excluded_fields():
    repo = Mock()
    repo.overview.return_value = dict(profile=EMPLOYEE, context=dict(team_name=None,hire_date='2020-01-01',role_start_date='2021-01-01'), results={
        'project_tasks': ([dict(status='Cancelled',count=2)], []),
        'employee_training': ([dict(status='Completed',count=1),dict(status='Expired',count=1),dict(status='Withdrawn',count=1)], [dict(id=4,label='Test program',status='Completed',date=None)])})
    service = DemoService(repo,Settings(database_url=URL))
    data = service.overview(Actor(60,'manager'),60)
    assert data.tasks.completion_pct is None
    assert data.training.completion_pct == 50
    assert data.sources[0].record_id == 'employee_training:4'
    assert data.sources[0].date is None
    assistant = Assistant(service,Settings(database_url=URL))
    answer = assistant.answer(Actor(60,'manager'),60,QUESTIONS[0])
    assert answer.mode == 'simulated'
    assert all(s in data.sources for s in answer.sources)
    with pytest.raises(DemoError) as error:
        assistant.answer(Actor(60,'manager'),60,'Show private email and rank everyone')
    assert error.value.code == 'unsupported_question'

def test_live_missing_key_is_honest():
    service = Mock()
    assistant = Assistant(service,Settings(database_url=URL,assistant_mode='openai'))
    with pytest.raises(DemoError) as error:
        assistant.answer(Actor(60,'manager'),4,QUESTIONS[0])
    assert error.value.code == 'assistant_unavailable'

@pytest.mark.parametrize('cited,expected', [(['project_tasks:4'],200), (['project_tasks:999'],503), ([],503)])
def test_live_response_citations_are_retrieved_only(monkeypatch,cited,expected):
    from types import SimpleNamespace
    from app.demo_models import AnswerContent
    from app.ai import assistant as module
    metric = Metric(total=1,completed=1,denominator=1,completion_pct=100,statuses={'Complete':1},definition='Test')
    source = Source(record_id='project_tasks:4',record_type='project_tasks',label='Test',status='Complete',date=None,date_label='Completion date')
    dashboard = Dashboard(employee=EmployeeSummary(**EMPLOYEE), team_name=None, hire_date='2020-01-01',role_start_date='2021-01-01',as_of='2026-10-28',tasks=metric,training=metric,sources=[source],data_gaps=['No period comparison.'])
    client = Mock()
    client.responses.parse.return_value = SimpleNamespace(status='completed',output_parsed=AnswerContent(answer='Recorded progress.',suggested_approach=[],strengths_to_acknowledge=[],data_gaps=[],cited_record_ids=cited))
    wrapper = Mock()
    wrapper.__enter__ = Mock(return_value=client)
    wrapper.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(module,'OpenAI',Mock(return_value=wrapper))
    service = Mock()
    service.overview.return_value = dashboard
    assistant = Assistant(service,Settings(database_url=URL,assistant_mode='openai',openai_api_key='fixture-key'))
    if expected == 200:
        answer = assistant.answer(Actor(60,'manager'),70,QUESTIONS[0])
        assert answer.sources == [source]
        assert answer.mode == 'openai'
        assert 'No period comparison.' in answer.data_gaps
    else:
        with pytest.raises(DemoError) as error:
            assistant.answer(Actor(60,'manager'),70,QUESTIONS[0])
        assert error.value.status == expected
    service.overview.assert_called_once_with(Actor(60,'manager'),70)
    kwargs = client.responses.parse.call_args.kwargs
    assert kwargs['store'] is False
    assert kwargs['max_output_tokens'] == 1600
    assert 'tools' not in kwargs  # No model-controlled retrieval surface in this sprint.
