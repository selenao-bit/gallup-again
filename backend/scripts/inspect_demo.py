"""Read-only sprint mapping evidence; no credentials or narrative text printed."""
from app.config import Settings
from app.database import Database
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

if __name__ == '__main__':
    db = Database(Settings.from_environment())
    try:
        with db.read() as c:
            print('read_only:', c.execute(text('SHOW transaction_read_only')).scalar_one())
            for table in ['employees', 'positions', 'departments', 'teams', 'project_tasks', 'employee_training']:
                print(table, [tuple(r) for r in c.execute(text('SELECT column_name, data_type FROM information_schema.columns WHERE table_schema=\'public\' AND table_name=:table ORDER BY ordinal_position'), {'table': table})])
            print('manager_candidates:', [dict(r) for r in c.execute(text("""SELECT e.employee_id, count(r.employee_id) AS reports,
                (SELECT count(*) FROM project_tasks t WHERE t.employee_id IN (SELECT employee_id FROM employees WHERE supervisor_id=e.employee_id AND employee_id<>e.employee_id)) AS tasks
                FROM employees e JOIN employees r ON r.supervisor_id=e.employee_id AND r.employee_id<>e.employee_id AND r.employment_status IN ('Active','Leave')
                WHERE e.employment_status='Active' GROUP BY e.employee_id ORDER BY tasks DESC, e.employee_id LIMIT 5""")).mappings()])
            print('active_ids:', c.execute(text("SELECT employee_id FROM employees WHERE employment_status='Active' ORDER BY employee_id LIMIT 5")).scalars().all())
            for table in ['project_tasks','employee_training']:
                print(table, c.execute(text(f'SELECT count(*) FROM {table}')).scalar_one())
    except SQLAlchemyError:
        print('Database inspection unavailable; no connection details displayed.')
        raise SystemExit(1) from None
    finally:
        db.close()
