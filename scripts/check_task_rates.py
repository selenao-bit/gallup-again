"""Read-only population rate check plus representative employee API checks."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from collections import defaultdict
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.config import Settings
from app.database import Database
from app.services.progress import completion_metric
from app.main import create_app

settings=Settings.from_environment().model_copy(update={'demo_identity_enabled':True})
statuses=defaultdict(dict);active=set()
with Database(settings).read() as c:
    for r in c.execute(text('''SELECT e.employee_id,e.employment_status,t.task_status,count(t.task_id) AS rows
        FROM public.employees e LEFT JOIN public.project_tasks t ON t.employee_id=e.employee_id
        GROUP BY e.employee_id,e.employment_status,t.task_status ORDER BY e.employee_id''')).mappings():
        if r['employment_status']=='Active':active.add(r['employee_id'])
        statuses[r['employee_id']]
        if r['task_status'] is not None:statuses[r['employee_id']][r['task_status']]=r['rows']
rates={key:completion_metric(values,'tasks') for key,values in statuses.items()}
assert len(rates)==2500
counts={'numeric':0,'no_assigned_tasks':0,'cancelled_only':0};examples={}
for key,metric in rates.items():
    assert metric.completed<=metric.denominator<=metric.total
    state='no_assigned_tasks' if metric.total==0 else 'cancelled_only' if metric.denominator==0 else 'numeric'
    counts[state]+=1
    if metric.completion_pct is not None:
        assert metric.completion_pct==round(100*metric.completed/metric.denominator,1)
    if key in active:examples.setdefault(state,key)
with TestClient(create_app(settings)) as client:
    for state,key in examples.items():
        response=client.get('/employee/record',headers={'X-Demo-Employee-Id':str(key)})
        assert response.status_code==200
        assert response.json()['task_progress']==rates[key].model_dump(mode='json')
print('Task metrics verified for all',len(rates),'employees:',counts)
print('Employee API metrics verified for:',', '.join(sorted(examples)))
