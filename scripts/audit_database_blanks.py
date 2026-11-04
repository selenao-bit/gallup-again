"""Inventory NULL/empty/placeholder fields with SELECT-only access; no field values printed."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from sqlalchemy import text
from app.config import Settings
from app.database import Database


def identifier(value):
    return '"'+value.replace('"','""')+'"'


def main():
    db=Database(Settings.from_environment())
    tables=[]
    with db.read() as c:
        names=c.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")).scalars().all()
    for name in names:
        with db.read() as c:
            columns=c.execute(text("SELECT column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name=:table ORDER BY ordinal_position"),{'table':name}).mappings().all()
            fields=['count(*) AS rows']
            for i,col in enumerate(columns):
                q=identifier(col['column_name'])
                fields.append(f'count(*) FILTER (WHERE {q} IS NULL) AS null_{i}')
                if col['data_type'] in {'text','character varying','character'}:
                    fields.append(f"count(*) FILTER (WHERE {q} IS NOT NULL AND btrim({q})='') AS empty_{i}")
                    fields.append(f"count(*) FILTER (WHERE lower(btrim({q})) IN ('n/a','na','null','none')) AS placeholder_{i}")
            row=c.execute(text('SELECT '+', '.join(fields)+' FROM public.'+identifier(name))).mappings().one()
            missing=[]
            for i,col in enumerate(columns):
                missing.append({**dict(col),'nulls':row[f'null_{i}'],'empty_strings':row.get(f'empty_{i}',0),'placeholder_strings':row.get(f'placeholder_{i}',0)})
            tables.append({'table':name,'rows':row['rows'],'columns':missing})
    with db.read() as c:
        rates=c.execute(text('''WITH task_counts AS (
            SELECT employee_id,count(*) AS total,count(*) FILTER (WHERE task_status<>'Cancelled') AS eligible,
            count(*) FILTER (WHERE task_status='Complete') AS completed FROM public.project_tasks GROUP BY employee_id)
            SELECT e.employment_status,count(*) AS employees,
            count(*) FILTER (WHERE COALESCE(t.total,0)=0) AS no_tasks,
            count(*) FILTER (WHERE COALESCE(t.eligible,0)=0) AS no_eligible_tasks,
            count(*) FILTER (WHERE t.eligible>0) AS numeric_rate_available
            FROM public.employees e LEFT JOIN task_counts t ON t.employee_id=e.employee_id GROUP BY e.employment_status ORDER BY e.employment_status''')).mappings().all()
        review_rates=c.execute(text('''SELECT count(*) AS rows,count(*) FILTER (WHERE task_completion_pct IS NULL) AS null_task_pct,
            count(*) FILTER (WHERE task_completion_pct IS NULL AND review_period IS NOT NULL) AS null_task_pct_with_period FROM public.performance_reviews''')).mappings().one()
    db.close()
    report={'access':'SELECT-only','tables':tables,'task_coverage':[dict(r) for r in rates],'review_task_completion':dict(review_rates)}
    output=Path(__file__).resolve().parents[1]/'local-fixtures/data-audit/before.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        output=output.with_name('latest.json')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('Audit saved:',output)
    for table in tables:
        missing=[c for c in table['columns'] if c['nulls'] or c['empty_strings'] or c['placeholder_strings']]
        print(table['table'],'rows',table['rows'],'missing:', ', '.join(f"{c['column_name']}={c['nulls']} NULL/{c['empty_strings']} empty/{c['placeholder_strings']} marker" for c in missing) or 'none')
    print('Task coverage:',json.dumps(report['task_coverage']))
    print('Review task rates:',json.dumps(report['review_task_completion']))

if __name__=='__main__':
    try:main()
    except Exception as error:
        raise SystemExit('Read-only audit failed ('+type(error).__name__+').') from None
