"""Read-only functional smoke checks against configured existing corporate data."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

settings=Settings.from_environment().model_copy(update={'demo_identity_enabled':True})
with TestClient(create_app(settings)) as c:
    catalog=c.get('/demo/personas')
    assert catalog.status_code==200
    personas=catalog.json()['personas']
    manager=next(p for p in personas if p['role']=='manager')
    employee=next(p for p in personas if p['role']=='employee')
    h={'X-Demo-Employee-Id':str(employee['employee_id'])}
    record=c.get('/employee/record',headers=h)
    assert record.status_code==200,record.status_code
    assert record.json()['employee']['employee_id']==employee['employee_id']
    for r in record.json()['records']:
        assert not {'manager_notes','reviewer_id'} & r['fields'].keys()
    assert c.get('/employee/record?employee_id=1',headers=h).status_code==422
    assert c.get('/manager/reports',headers=h).status_code==403
    inbox=c.get('/employee/emails',headers=h)
    engagement=c.get('/employee/engagement',headers=h)
    assert inbox.status_code==engagement.status_code==200
    assert c.get('/employee/emails?employee_id=1',headers=h).status_code==422
    mh={'X-Demo-Employee-Id':str(manager['employee_id'])}
    reports=c.get('/manager/reports',headers=mh).json()['reports']
    assert reports
    subject=reports[0]['employee_id']
    assert c.get(f'/manager/reports/{subject}/dashboard',headers=mh).status_code==200
    bundle=c.get(f'/manager/reports/{subject}/record',headers=mh)
    assert bundle.status_code==200
    assert not {'reviews','self_assessments'} & bundle.json()['counts'].keys()
    assert c.get(f"/manager/reports/{manager['employee_id']}/record",headers=mh).status_code==404
    assert c.get(f"/manager/reports/{manager['employee_id']}/dashboard",headers=mh).status_code==404
    print('Read-only integration smoke passed.')
    print('Active synthetic personas:',len(personas))
    print('Employee category counts:',record.json()['counts'])
    print('Visible email messages:',len(inbox.json()['messages']))
    print('Q12 survey waves:',len(engagement.json()['surveys']))
    print('Manager direct reports checked:',len(reports))
