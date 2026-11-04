"""Focused integration checks; no corporate database or external model is used."""
from contextlib import contextmanager
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from app.main import create_app
from app.config import Settings
from app.services.access import Actor, DemoError
from app.repositories.workspace import WorkspaceRepository, PROJECTIONS

URL='postgresql://test:test@localhost/test'

def client_fixture(enabled=True):
    app=create_app(Settings(database_url=URL,demo_identity_enabled=enabled))
    repo=Mock()
    repo.persona.side_effect=lambda n:dict(employee_id=n,display_name=f'Person {n}',position_title='Analyst',department_name=None,employment_status='Active') if n in {1,2} else None
    repo.has_reports.side_effect=lambda n:n==1
    app.state.workspace_service.repository=repo
    app.state.workspace_repository=repo
    return app,repo

def test_employee_scope_is_session_pinned():
    app,repo=client_fixture()
    repo.emails.return_value={'messages':[]}
    with TestClient(app) as c:
        assert c.get('/employee/emails').status_code==401
        assert c.get('/employee/emails',headers={'X-Demo-Employee-Id':'2'}).status_code==200
        assert repo.emails.call_args.args==(Actor(2,'employee'),None)
        assert c.get('/employee/emails?employee_id=1',headers={'X-Demo-Employee-Id':'2'}).status_code==422
        assert c.post('/employee/chat',headers={'X-Demo-Employee-Id':'2'},json={'question':'hello','employee_id':1}).status_code==422
        assert c.get('/manager/reports/1/record',headers={'X-Demo-Employee-Id':'2'}).status_code==403
        assert c.get('/manager/reports/1/record',headers={'X-Demo-Employee-Id':'1'}).status_code==404

def test_disabled_employee_routes_fail_before_reading():
    app,repo=client_fixture(False)
    with TestClient(app) as c:
        for path in ['/employee/record','/employee/emails','/employee/engagement']:
            r=c.get(path,headers={'X-Demo-Employee-Id':'2'})
            assert r.status_code==404
            assert r.headers['cache-control']=='no-store'
    repo.persona.assert_not_called()

def test_sensitive_columns_are_not_projected():
    projections=' '.join(p[-1] for p in PROJECTIONS.values())
    for private in ['manager_notes','reviewer_id','sender_id']:
        assert private not in projections

def test_message_participation_and_bcc_are_enforced_in_sql():
    engine=create_engine('sqlite://',poolclass=StaticPool)
    with engine.begin() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS public"))
        for ddl in [
            'CREATE TABLE public.employees(employee_id INTEGER,employee_fname TEXT,employee_lname TEXT)',
            'CREATE TABLE public.email_accounts(employee_id INTEGER,email_address TEXT)',
            'CREATE TABLE public.email_records(email_id INTEGER,thread_id INTEGER,sender_id INTEGER,sent_at TEXT,subject TEXT,body TEXT,reply_to_id INTEGER,has_attachments BOOLEAN)',
            'CREATE TABLE public.email_recipients(email_id INTEGER,recipient_id INTEGER,recipient_type TEXT)',
        ]:c.execute(text(ddl))
        c.execute(text("INSERT INTO public.employees VALUES (1,'A','One'),(2,'B','Two'),(3,'C','Three'),(4,'D','Four')"))
        c.execute(text("INSERT INTO public.email_records VALUES (10,7,1,'2026-01-01','Visible','Message A',NULL,false),(11,7,3,'2026-01-02','Hidden','Message B',10,false)"))
        c.execute(text("INSERT INTO public.email_recipients VALUES (10,2,'to'),(10,4,'bcc'),(11,4,'to')"))
    class DB:
        @contextmanager
        def read(self):
            with engine.connect() as c:yield c
    repo=WorkspaceRepository(DB())
    received=repo.emails(Actor(2,'employee'),None)['messages']
    assert [m['email_id'] for m in received]==[10]  # Same thread does not expose 11.
    assert [r['recipient_id'] for r in received[0]['recipients']]==[2]
    sent=repo.emails(Actor(1,'manager'),None)['messages']
    assert {r['recipient_id'] for r in sent[0]['recipients']}=={2,4}
    assert repo.emails(Actor(3,'employee'),None)['messages'][0]['email_id']==11
    assert repo.emails(Actor(2,'employee'),10)['messages']==[]
    engine.dispose()

def test_no_model_call_when_unconfigured_and_access_checked_first():
    from app.ai.workspace import WorkspaceAssistant
    repo=Mock()
    assistant=WorkspaceAssistant(repo,Settings(database_url=URL))
    with pytest.raises(DemoError) as e:assistant.answer(Actor(2,'employee'),1,'hello')
    assert e.value.status==403
    repo.bundle.assert_not_called()
    with pytest.raises(DemoError) as e:assistant.answer(Actor(2,'employee'),2,'hello')
    assert e.value.code=='assistant_unavailable'
    repo.bundle.assert_called_once_with(Actor(2,'employee'),2)

@pytest.mark.parametrize('cited,valid',[(['employee_goals:2'],True),(['employee_goals:999'],False),([],False)])
def test_workspace_ai_validates_source_ids_and_bounds_text(monkeypatch,cited,valid):
    from types import SimpleNamespace
    from app.ai import workspace as module
    from app.workspace_models import Record, RecordBundle, WorkspaceAnswer
    from app.demo_models import EmployeeSummary
    repo=Mock()
    repo.bundle.return_value=RecordBundle(employee=EmployeeSummary(employee_id=2,display_name='Test',position_title='Analyst',department_name=None,employment_status='Active'),records=[Record(record_id='employee_goals:2',category='goals',title='Goal',fields={'description':'x'*3000})],counts={'goals':1},gaps=[])
    answer=WorkspaceAnswer(answer='A sourced answer.',discussion_questions=[],data_gaps=[],cited_record_ids=cited)
    client=Mock()
    client.responses.parse.return_value=SimpleNamespace(output_parsed=answer,status='completed')
    factory=Mock()
    factory.return_value.__enter__=Mock(return_value=client)
    factory.return_value.__exit__=Mock(return_value=False)
    monkeypatch.setattr(module,'create_client',factory)
    assistant=module.WorkspaceAssistant(repo,Settings(database_url=URL,assistant_mode='openai',openai_api_key='test-only'))
    if valid:
        result=assistant.answer(Actor(2,'employee'),2,'What is my goal?')
        assert result.sources[0].record_id=='employee_goals:2'
    else:
        with pytest.raises(DemoError) as error:assistant.answer(Actor(2,'employee'),2,'What is my goal?')
        assert error.value.code=='assistant_unavailable'
    kwargs=client.responses.parse.call_args.kwargs
    assert kwargs['store'] is False
    assert 'tools' not in kwargs
    assert 'x'*1201 not in kwargs['input'][1]['content']
    repo.bundle.assert_called_once_with(Actor(2,'employee'),2)

@pytest.mark.parametrize('mode,key,expected',[('simulated','private-test-key',False),('openai','',False),('openai','private-test-key',True)])
def test_catalog_reports_ai_readiness_without_exposing_key(mode,key,expected):
    from app.services.workspace import WorkspaceService
    repo=Mock()
    repo.personas.return_value=[{'employee_id':2,'display_name':'Synthetic','has_reports':False}]
    service=WorkspaceService(repo,Settings(database_url=URL,assistant_mode=mode,openai_api_key=key))
    catalog=service.personas()
    assert catalog.assistant_available is expected
    assert 'private-test-key' not in catalog.model_dump_json()


def test_rate_limit_error_is_actionable_and_does_not_expose_provider_body(monkeypatch):
    from app.ai import workspace as module
    from app.workspace_models import RecordBundle
    from app.demo_models import EmployeeSummary
    from openai import RateLimitError
    import httpx
    repo=Mock()
    repo.bundle.return_value=RecordBundle(employee=EmployeeSummary(employee_id=2,display_name='Test',position_title='Analyst',department_name=None,employment_status='Active'),records=[],counts={},gaps=[])
    response=httpx.Response(429,request=httpx.Request('POST','https://example.test/responses'))
    wrapper=Mock();client=Mock()
    wrapper.__enter__=Mock(return_value=client);wrapper.__exit__=Mock(return_value=False)
    client.responses.parse.side_effect=RateLimitError('private-provider-details',response=response,body={'message':'private-provider-details'})
    monkeypatch.setattr(module,'create_client',Mock(return_value=wrapper))
    assistant=module.WorkspaceAssistant(repo,Settings(database_url=URL,assistant_mode='openai',openai_api_key='test-only'))
    with pytest.raises(DemoError) as error:assistant.answer(Actor(2,'employee'),2,'hello')
    assert error.value.status==429 and error.value.code=='assistant_rate_limited'
    assert 'private-provider-details' not in error.value.message
