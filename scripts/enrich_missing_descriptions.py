"""Fill authorized missing narrative context only; preserve structured/known values."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from app.config import Settings

RULES=[
 ('positions','position_id','description',"""'[Synthetic role context v1] Recorded role: ' || t.position_title ||
    '. Department: ' || t.department_name || '. Seniority: ' || COALESCE(t.seniority_level,'not recorded') ||
    '. This summary describes the existing role record; it does not define new duties, competencies or performance expectations.'"""),
 ('projects','project_id','description',"""'[Synthetic project context v1] ' || t.project_name || '. Recorded type: ' ||
    COALESCE(t.type,'not recorded') || '. Status: ' || t.status || '. Planned start: ' || t.start_date::date::text ||
    '. Target end: ' || COALESCE(t.target_end_date::date::text,'not recorded') ||
    '. Actual end: ' || COALESCE(t.actual_end_date::date::text,'not applicable while unfinished or cancelled') ||
    '. Dates and status summarize the source record; no new outcome is asserted.'"""),
 ('project_tasks','task_id','description',"""'[Synthetic task context v1] ' || t.title || '. Project ID: ' || t.project_id::text ||
    '. Recorded priority: ' || t.priority || '. Complexity: ' || COALESCE(t.complexity,'not recorded') ||
    '. Status: ' || t.task_status || '. Due date: ' || COALESCE(t.due_date::text,'not recorded') ||
    '. Estimated hours: ' || COALESCE(t.estimated_hours::text,'not recorded') ||
    '. This is context for discussing the existing assignment, not evidence of an additional accomplishment.'"""),
 ('employee_goals','goal_id','complete_desc',"""'[Synthetic goal context v1] ' || t.goal_description || '. Recorded status: ' ||
    COALESCE(t.complete_status,'not recorded') || '. Recorded plan: ' || COALESCE(t.start_date::date::text,'not recorded') ||
    ' to ' || COALESCE(t.end_date::date::text,'not recorded') ||
    '. Review the source status and discuss supporting evidence or needed support. The goal end date is a planned period boundary, not a verified completion timestamp.'""")]


def missing(field):
    return f"({field} IS NULL OR lower(btrim({field})) IN ('','n/a','na'))"


def invariant(c,table,key,field):
    return c.execute(text(f"SELECT md5(COALESCE(string_agg(md5((to_jsonb(t)-CAST(:field AS text))::text),'' ORDER BY t.{key}),'')) FROM public.{table} t"),{'field':field}).scalar_one()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    settings=Settings.from_environment()
    engine=create_engine(make_url(settings.database_url.get_secret_value()).set(drivername='postgresql+psycopg'),hide_parameters=True,
        connect_args={'connect_timeout':3,'options':'-c lock_timeout=3000 -c statement_timeout=30000'+('' if args.apply else ' -c default_transaction_read_only=on')})
    report={'status':'applied' if args.apply else 'preview','fields':[]}
    with engine.begin() as c:
        if args.apply:c.execute(text('LOCK TABLE public.positions,public.projects,public.project_tasks,public.employee_goals,public.q12_questions IN SHARE ROW EXCLUSIVE MODE'))
        for table,key,field,expression in RULES:
            count=c.execute(text(f'SELECT count(*) FROM public.{table} WHERE '+missing(field))).scalar_one()
            before=invariant(c,table,key,field)
            existing={r[0]:r[1] for r in c.execute(text(f'SELECT {key},{field} FROM public.{table} WHERE NOT '+missing(field)))}
            preview=[dict(r) for r in c.execute(text(f'SELECT t.{key} AS id,{expression} AS proposed_text FROM public.{table} t WHERE '+missing('t.'+field)+f' ORDER BY t.{key} LIMIT 2')).mappings()]
            item={'table':table,'column':field,'missing_before':count,'structured_hash_before':before,'preview':preview}
            if args.apply:
                result=c.execute(text(f'UPDATE public.{table} t SET {field}={expression} WHERE '+missing('t.'+field)))
                assert result.rowcount==count
                assert c.execute(text(f'SELECT count(*) FROM public.{table} WHERE '+missing(field))).scalar_one()==0
                assert invariant(c,table,key,field)==before,'Structured fields changed.'
                for row in c.execute(text(f'SELECT {key},{field} FROM public.{table}')):
                    if row[0] in existing:assert existing[row[0]]==row[1],'Existing text changed.'
                item['updated']=result.rowcount;item['structured_hash_after']=before
            report['fields'].append(item)
        # Q00 already exists; its reference fixture explicitly calls this Overall Satisfaction.
        q00=c.execute(text("SELECT element FROM public.q12_questions WHERE id='Q00'")).scalar_one()
        if args.apply and (q00 is None or not q00.strip()):
            c.execute(text("UPDATE public.q12_questions SET element='Overall Satisfaction' WHERE id='Q00' AND (element IS NULL OR btrim(element)='')"))
            report['q00_element_updated']=1
        else:report['q00_element_updated']=0
    engine.dispose()
    output=Path(__file__).resolve().parents[1]/'local-fixtures/data-audit'/('description-enrichment.json' if args.apply else 'description-preview.json')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'narrative_fields':sum(f.get('updated',0) for f in report['fields']),
                      'q00_element_updated':report['q00_element_updated'],'preview_file':str(output)}))

if __name__=='__main__':
    try:main()
    except Exception as error:raise SystemExit('Description enrichment failed ('+type(error).__name__+'); verify current counts before retrying.') from None
