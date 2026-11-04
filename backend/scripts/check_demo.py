"""Explicit read-only live smoke check. Never creates or modifies corporate records."""
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.config import Settings
from app.main import create_app
from app.demo_models import QUESTIONS

if __name__ == '__main__':
    app = create_app(Settings.from_environment().model_copy(update={'demo_identity_enabled':True, 'assistant_mode':'simulated'}))
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status':'ok'}
        assert client.get('/health/db').status_code == 200
        catalog = client.get('/demo/personas')
        assert catalog.status_code == 200, catalog.status_code
        assert {p['employee_id'] for p in catalog.json()['personas']} == {1,2,60}
        headers = {'X-Demo-Employee-Id':'60'}
        assert client.get('/demo/me', headers=headers).status_code == 200
        reports, cursor = [], None
        while True:
            path = '/manager/reports?limit=50' + (f'&after_employee_id={cursor}' if cursor is not None else '')
            page = client.get(path,headers=headers)
            assert page.status_code == 200, page.json()
            reports += page.json()['reports']
            cursor = page.json()['next_after_employee_id']
            if cursor is None: break
        with app.state.database.read() as c:
            expected = c.execute(text("SELECT employee_id FROM employees WHERE supervisor_id=60 AND employee_id<>60 AND employment_status IN ('Active','Leave') ORDER BY employee_id")).scalars().all()
            assert [r['employee_id'] for r in reports] == expected
        print('Verified paginated current reports:',len(reports))
        selected = reports[0]['employee_id']
        response = client.get(f'/manager/reports/{selected}/dashboard',headers=headers)
        assert response.status_code == 200, response.json()
        dashboard = response.json()
        with app.state.database.read() as c:
            for category, table, column, done, excluded in [('tasks','project_tasks','task_status','Complete','Cancelled'),('training','employee_training','completion_status','Completed','Withdrawn')]:
                rows = c.execute(text(f'SELECT {column} AS status, count(*) AS total FROM {table} WHERE employee_id=:id GROUP BY {column}'),{'id':selected}).mappings().all()
                counts = {r['status']:r['total'] for r in rows}
                assert dashboard[category]['statuses'] == counts
                assert dashboard[category]['denominator'] == sum(counts.values())-counts.get(excluded,0)
                assert dashboard[category]['completed'] == counts.get(done,0)
            for source in dashboard['sources']:
                table, value = source['record_id'].split(':')
                key = 'task_id' if table=='project_tasks' else 'training_id'
                assert c.execute(text(f'SELECT employee_id FROM {table} WHERE {key}=:id'),{'id':int(value)}).scalar_one() == selected
        answer = client.post(f'/manager/reports/{selected}/chat',headers=headers,json={'question':QUESTIONS[0]})
        assert answer.status_code == 200, answer.json()
        assert answer.json()['mode'] == 'simulated'
        assert {s['record_id'] for s in answer.json()['sources']} <= {s['record_id'] for s in dashboard['sources']}
        assert client.get('/manager/reports/60/dashboard',headers=headers).status_code == 404
        assert client.get('/manager/reports/1/dashboard',headers=headers).status_code == 404
        assert client.get('/manager/reports',headers={'X-Demo-Employee-Id':'1'}).status_code == 403
        assert client.get('/manager/reports',headers={'X-Demo-Employee-Id':'2'}).status_code == 403
        assert client.post(f'/manager/reports/{selected}/chat',headers=headers,json={'question':'Read private email'}).status_code == 422
        print('Verified overview counts, real source ownership, simulated answer, role/subject/category denials; subject:',selected)
