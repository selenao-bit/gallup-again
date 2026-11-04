"""Retrieval integration without external models or corporate writes."""
from contextlib import contextmanager
from unittest.mock import Mock
from sqlalchemy import create_engine,text
from sqlalchemy.pool import StaticPool
import pytest
from app.services.access import Actor,DemoError
from app.services.retrieval import retrieve
from app.repositories.workspace import WorkspaceRepository
from app.workspace_models import Record,RecordBundle
from app.demo_models import EmployeeSummary


def bundle():
    return RecordBundle(employee=EmployeeSummary(employee_id=2,display_name='Synthetic',position_title='Test',department_name=None,employment_status='Active'),records=[Record(record_id='employee_goals:1',category='goals',title='Goal',fields={})],counts={'goals':1},gaps=[])


def test_email_question_uses_email_sources_with_pinned_scope():
    repo=Mock();repo.bundle.return_value=bundle()
    repo.email_context.return_value=[Record(record_id='email_records:8',category='email',title='Work email',fields={'body':'Synthetic'})]
    records,gaps=retrieve(repo,Actor(1,'manager'),2,'What do my recent emails discuss?')
    assert [r.record_id for r in records]==['email_records:8']
    repo.bundle.assert_called_once_with(Actor(1,'manager'),2)
    repo.email_context.assert_called_once_with(Actor(1,'manager'),2,[])
    repo.engagement.assert_not_called()
    assert any('synthetic' in g for g in gaps)


def test_q12_keeps_composite_citations_and_excludes_suppressed_values():
    repo=Mock();repo.bundle.return_value=bundle()
    repo.engagement.return_value={'groups':[{'group_id':3,'group_name':'Team'}],
        'surveys':[{'survey_id':2,'reporting_period':'2026-H1','end_date':'2026-04-21'},{'survey_id':1,'reporting_period':'2025-H2','end_date':'2025-10-21'}],
        'results':[{'group_id':3,'survey_id':2,'suppressed':False,'items':[{'question_id':'Q01','text':'Clear expectations','mean_score':4.2}]},
                   {'group_id':3,'survey_id':1,'suppressed':True,'items':[]}]}
    records,gaps=retrieve(repo,Actor(1,'manager'),2,'Compare Q12 waves.')
    assert [r.record_id for r in records]==['q12_results:2:3:Q01']
    assert records[0].date=='2026-04-21'
    repo.engagement.assert_called_once_with(Actor(1,'manager'),2)
    repo.email_context.assert_not_called()
    assert any('suppressed' in g for g in gaps)


def test_unrelated_work_question_does_not_retrieve_email_or_q12():
    repo=Mock();repo.bundle.return_value=bundle()
    records,_=retrieve(repo,Actor(2,'employee'),2,'What are my goals?')
    assert records[0].category=='goals'
    repo.email_context.assert_not_called();repo.engagement.assert_not_called()


def test_scoped_email_search_and_reporting_changes():
    engine=create_engine('sqlite://',poolclass=StaticPool)
    with engine.begin() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS public"))
        c.execute(text('CREATE TABLE public.employees(employee_id INTEGER,supervisor_id INTEGER,employment_status TEXT)'))
        c.execute(text('CREATE TABLE public.email_records(email_id INTEGER,thread_id INTEGER,sender_id INTEGER,sent_at TEXT,subject TEXT,body TEXT)'))
        c.execute(text('CREATE TABLE public.email_recipients(email_id INTEGER,recipient_id INTEGER,recipient_type TEXT)'))
        c.execute(text("INSERT INTO public.employees VALUES (1,1,'Active'),(2,1,'Active'),(3,1,'Active'),(4,4,'Active')"))
        c.execute(text("INSERT INTO public.email_records VALUES (10,7,1,'2026-01-01','Training','Synthetic course discussion'),(11,7,2,'2026-01-02','Goal','Private to employee and colleague'),(12,9,1,'2026-01-03','Other report','Other work')"))
        c.execute(text("INSERT INTO public.email_recipients VALUES (10,2,'to'),(11,3,'to'),(12,3,'bcc')"))
    class DB:
        @contextmanager
        def read(self):
            with engine.connect() as c:yield c
    repo=WorkspaceRepository(DB())
    messages=repo.email_context(Actor(1,'manager'),2,[])
    assert [r.record_id for r in messages]==['email_records:10']
    assert 'recipients' not in messages[0].fields
    assert [r.record_id for r in repo.email_context(Actor(2,'employee'),2,['course'])]==['email_records:10']
    assert [r.record_id for r in repo.email_context(Actor(2,'employee'),2,[])]==['email_records:11','email_records:10']
    assert repo.email_context(Actor(4,'manager'),2,[])==[]
    with pytest.raises(DemoError):repo.email_context(Actor(2,'employee'),3,[])
    with engine.begin() as c:c.execute(text('UPDATE public.employees SET supervisor_id=4 WHERE employee_id=2'))
    assert repo.email_context(Actor(1,'manager'),2,[])==[]
    # Current actor participation does not grant a new manager old inbox messages.
    assert repo.email_context(Actor(4,'manager'),2,[])==[]
    engine.dispose()


def q12_fixture():
    groups=[{'group_id':1,'group_name':'Company','group_type':'Company'},{'group_id':3,'group_name':'Team','group_type':'Team'}]
    surveys=[{'survey_id':2,'reporting_period':'2026-H1','end_date':'2026-04-21'},{'survey_id':1,'reporting_period':'2025-H2','end_date':'2025-10-21'}]
    results=[{'group_id':g['group_id'],'survey_id':s['survey_id'],'suppressed':False,'items':[{'question_id':'Q01','text':'Expectations','mean_score':4}]} for g in groups for s in surveys]
    return {'groups':groups,'surveys':surveys,'results':results}


def test_q12_defaults_to_most_specific_permitted_group_latest_wave():
    repo=Mock();repo.bundle.return_value=bundle();repo.engagement.return_value=q12_fixture()
    records,gaps=retrieve(repo,Actor(2,'employee'),2,'Summarize Q12 engagement.')
    assert [r.record_id for r in records]==['q12_results:2:3:Q01']
    assert any('2026-H1' in g and 'Team' in g for g in gaps)


def test_q12_explicit_group_and_wave_are_honored_within_scope():
    repo=Mock();repo.bundle.return_value=bundle();repo.engagement.return_value=q12_fixture()
    records,_=retrieve(repo,Actor(2,'employee'),2,'Prepare Q12 group 1 and survey 1.')
    assert [r.record_id for r in records]==['q12_results:1:1:Q01']
    records,gaps=retrieve(repo,Actor(2,'employee'),2,'Prepare Q12 group 999 and survey 1.')
    assert not records and any('unavailable' in g for g in gaps)


def test_q12_explicit_comparison_keeps_both_waves():
    repo=Mock();repo.bundle.return_value=bundle();repo.engagement.return_value=q12_fixture()
    records,_=retrieve(repo,Actor(2,'employee'),2,'Compare company Q12 waves.')
    assert [r.record_id for r in records]==['q12_results:2:1:Q01','q12_results:1:1:Q01']
