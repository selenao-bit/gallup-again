"""SELECT-only exact read-back checks for the approved email and Q12 import."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from sqlalchemy import text
from import_demo_fixtures import convert,load_csv
from app.config import Settings
from app.database import Database

ROOT=Path(__file__).resolve().parents[1]
with Database(Settings.from_environment()).read() as c:
    for table,directory,kind,keys in [
        ('email_records','emails','emails',['email_id']),
        ('email_recipients','emails','recipients',['email_id','recipient_id','recipient_type']),
        ('q12_surveys','q12','surveys',['survey_id']),
        ('q12_results','q12','results',['survey_id','group_id','question_id'])]:
        rows=convert(load_csv(ROOT/'local-fixtures'/directory/(table+'.csv')),kind)
        columns=list(rows[0])
        live=[dict(r) for r in c.execute(text(f"SELECT {', '.join(columns)} FROM public.{table} ORDER BY {', '.join(keys)}")).mappings()]
        expected=sorted(rows,key=lambda r:tuple(r[k] for k in keys))
        assert live==expected,table+' differs from approved fixtures'
        print(table+': exact read-back passed for '+str(len(live))+' rows')
    questions=load_csv(ROOT/'local-fixtures/q12/q12_questions.csv')
    current={r['id']:r['text'] for r in c.execute(text('SELECT id,text FROM public.q12_questions')).mappings()}
    assert current=={r['id']:r['text'] for r in questions}
    assert c.execute(text('''SELECT count(*) FROM public.q12_results WHERE is_suppressed AND
        (mean_score IS NOT NULL OR top_box_pct IS NOT NULL OR score_1_count IS NOT NULL OR score_2_count IS NOT NULL OR score_3_count IS NOT NULL OR score_4_count IS NOT NULL OR score_5_count IS NOT NULL)''')).scalar_one()==0
    assert c.execute(text('''SELECT count(*) FROM public.q12_results WHERE NOT is_suppressed AND
        (response_count<>score_1_count+score_2_count+score_3_count+score_4_count+score_5_count OR
        abs(mean_score-1.0*(score_1_count+2*score_2_count+3*score_3_count+4*score_4_count+5*score_5_count)/response_count)>1e-10 OR
        abs(top_box_pct-100.0*score_5_count/response_count)>1e-10)''')).scalar_one()==0
    covered=c.execute(text('''SELECT count(*) FROM public.employees e JOIN (
        SELECT sender_id AS employee_id FROM public.email_records
        UNION SELECT recipient_id AS employee_id FROM public.email_recipients
        ) participants ON participants.employee_id=e.employee_id''')).scalar_one()
    print('Email participant coverage:',covered,'employees')
    print('Q12 question wording, suppression and arithmetic: PASS')
