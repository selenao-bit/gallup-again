"""Check synthetic fixture semantics and reproducibility without database writes."""
import importlib.util
from datetime import datetime
from pathlib import Path

path=Path(__file__).resolve().parents[2]/'scripts/generate_email_fixtures.py'
spec=importlib.util.spec_from_file_location('email_fixture_generator',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_threads_are_reproducible_referenced_and_after_hire():
    people=[{'employee_id':1,'supervisor_id':1,'employment_status':'Active','hire_date':datetime(2024,1,1)},
            {'employee_id':2,'supervisor_id':1,'employment_status':'Active','hire_date':datetime(2026,1,1)}]
    source=[{'employee_id':2,'category':'training','source_table':'employee_training','source_id':18,
             'record_date':datetime(2026,3,1),'title':'SQL course','status':'Completed'}]
    first=module.build(people,source)
    assert first==module.build(people,source)
    messages,recipients,anchors=first
    assert len(messages)==len(recipients)==2 and len(anchors)==1
    assert messages[1]['reply_to_id']==messages[0]['email_id']
    assert messages[0]['thread_id']==messages[1]['thread_id']
    assert {m['sender_id'] for m in messages}=={1,2}
    assert {r['recipient_id'] for r in recipients}=={1,2}
    assert all('employee_training:18' in m['body'] for m in messages)
    assert all('[Synthetic email fixture;' in m['body'] for m in messages)
    assert 'Recorded status at the demo snapshot: Completed' in messages[0]['body']
    assert all(datetime.fromisoformat(m['sent_at'])>=people[1]['hire_date'] for m in messages)
    assert all(datetime.fromisoformat(m['sent_at'])<=module.SNAPSHOT for m in messages)


def test_missing_supervisor_or_future_sources_do_not_create_threads():
    people=[{'employee_id':1,'supervisor_id':1,'employment_status':'Active','hire_date':datetime(2024,1,1)}]
    source=[{'employee_id':1,'category':'goal','source_table':'employee_goals','source_id':9,
             'record_date':datetime(2027,1,1),'title':'Future goal','status':'In Progress'}]
    assert module.build(people,source)==([],[],[])
