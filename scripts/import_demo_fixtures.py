"""Validate prepared synthetic fixtures; writes require an explicit --apply.

Never runs at app startup. Imports into existing tables only, with no overwrite.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.config import Settings

ROOT=Path(__file__).resolve().parents[1]


def load_csv(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))


def validate_files(email_dir,q12_dir):
    manifest=json.loads((email_dir/'manifest.json').read_text())
    for name,digest in manifest['source_sha256'].items():
        assert Path(name).name==name
        assert hashlib.sha256((email_dir/name).read_bytes()).hexdigest()==digest,'Email file hash changed.'
    reviewed=json.loads((q12_dir/'review-preflight.json').read_text())
    for name,digest in reviewed['source_sha256'].items():
        assert Path(name).name==name
        assert hashlib.sha256((q12_dir/name).read_bytes()).hexdigest()==digest,'Q12 source hash changed.'
    emails=load_csv(email_dir/'email_records.csv')
    recipients=load_csv(email_dir/'email_recipients.csv')
    anchors=json.loads((email_dir/'source_anchors.json').read_text())
    surveys=load_csv(q12_dir/'q12_surveys.csv')
    results=load_csv(q12_dir/'q12_results.csv')
    assert len(emails)==manifest['records']==len(recipients)==2*len(anchors)
    assert len(surveys)==2 and len(results)==1534
    expected = {
        'emails': ['email_id','thread_id','sender_id','sent_at','subject','body','reply_to_id','has_attachments','is_internal'],
        'recipients': ['email_id','recipient_id','recipient_type'],
        'surveys': ['survey_id','start_date','end_date','reporting_period','eligible_employees','respondent_count'],
        'results': ['survey_id','group_id','question_id','response_count','mean_score','top_box_pct','score_1_count','score_2_count','score_3_count','score_4_count','score_5_count','benchmark_pct','is_suppressed'],
    }
    for key, rows in [('emails',emails),('recipients',recipients),('surveys',surveys),('results',results)]:
        assert rows and list(rows[0])==expected[key], 'Unexpected fixture columns.'

    ids={int(r['email_id']) for r in emails}
    assert len(ids)==len(emails)
    assert len({(r['email_id'],r['recipient_id'],r['recipient_type']) for r in recipients})==len(recipients)
    for row in emails:
        assert '[Synthetic email fixture;' in row['body']
        assert row['is_internal']=='true' and row['has_attachments']=='false'
        assert not row['reply_to_id'] or int(row['reply_to_id']) in ids
        assert datetime.fromisoformat(row['sent_at'])<=datetime(2026,9,30,12)
    for row in recipients:
        assert int(row['email_id']) in ids and row['recipient_type']=='to'
    for row in results:
        suppressed=row['is_suppressed']=='true'
        assert suppressed==(int(row['response_count'])<5)
        if suppressed:assert all(not row[k] for k in ['mean_score','top_box_pct']+[f'score_{i}_count' for i in range(1,6)])
        else:
            counts=[int(row[f'score_{i}_count']) for i in range(1,6)]
            assert sum(counts)==int(row['response_count'])
            assert abs(sum((i+1)*n for i,n in enumerate(counts))/sum(counts)-float(row['mean_score']))<1e-12
    return dict(emails=emails,recipients=recipients,anchors=anchors,surveys=surveys,results=results,
                questions=load_csv(q12_dir/'q12_questions.csv'),groups=load_csv(q12_dir/'q12_groups.csv'),
                references=load_csv(q12_dir/'source_reference_ids.csv'),reviewed=reviewed)


def check_database(c,data):
    counts={t:c.execute(text('SELECT count(*) FROM public.'+t)).scalar_one() for t in ['email_records','email_recipients','q12_surveys','q12_results']}
    assert not any(counts.values()),'A destination is nonempty; stop rather than overwrite.'
    people={r['employee_id']:dict(r) for r in c.execute(text('SELECT employee_id,supervisor_id,department_id,team_id,employment_status,hire_date FROM public.employees')).mappings()}
    reference={int(r['entity_id']):r for r in data['references'] if r['entity_type']=='employee'}
    assert set(people)==set(reference)
    for key,row in people.items():
        for field in ['supervisor_id','department_id','team_id','employment_status']:
            assert str(row[field])==reference[key][field], 'Employee membership changed.'
    groups={str(r['group_id']):dict(r) for r in c.execute(text('SELECT group_id,group_name,group_type,department_id,team_id,manager_id FROM public.q12_groups')).mappings()}
    assert set(groups)=={r['group_id'] for r in data['groups']}
    for row in data['groups']:
        assert all(('' if groups[row['group_id']][k] is None else str(groups[row['group_id']][k]))==v for k,v in row.items())
    current={r['id']:r['text'] for r in c.execute(text('SELECT id,text FROM public.q12_questions')).mappings()}
    old_texts={r['id']:r['database'] for r in data['reviewed']['question_differences'] if r['column']=='text'}
    assert set(current)=={r['id'] for r in data['questions']}
    corrections=[]
    for row in data['questions']:
        if current[row['id']]!=row['text']:
            assert current[row['id']]==old_texts.get(row['id']), 'Question wording changed since review.'
            corrections.append({'id':row['id'],'text':row['text']})
    accounts=set(c.execute(text('SELECT DISTINCT employee_id FROM public.email_accounts')).scalars())
    source_tables={'employee_goals':('goal_id','goal_description','complete_status','start_date'),
                   'project_tasks':('task_id','title','task_status','created_date'),
                   'employee_training':('training_id','program_name','completion_status','assigned_date')}
    snapshots={}
    for table,(key,title,status,event) in source_tables.items():
        snapshots[table]={r['source_id']:dict(r) for r in c.execute(text(f'SELECT {key} AS source_id,employee_id,{title} AS title,{status} AS status,{event} AS event FROM public.{table}')).mappings()}
    for anchor in data['anchors']:
        person=people[anchor['employee_id']]
        assert person['supervisor_id']==anchor['supervisor_id']
        assert {anchor['employee_id'],anchor['supervisor_id']}<=accounts
        table,key=anchor['source_record_id'].split(':')
        record=snapshots[table][int(key)]
        assert record['employee_id']==anchor['employee_id'] and record['title']==anchor['source_title'] and record['status']==anchor['source_status'],'Email source changed.'
        event=record['event']
        if isinstance(event,date) and not isinstance(event,datetime):event=datetime.combine(event,datetime.min.time())
        assert (event.isoformat() if event else None)==anchor['source_date']
    for row in data['emails']:
        sender=people[int(row['sender_id'])]
        assert datetime.fromisoformat(row['sent_at'])>=sender['hire_date']
    return corrections


def convert(rows,kind):
    converted=[]
    for row in rows:
        item={}
        for key,value in row.items():
            if value=='':item[key]=None
            elif key in {'subject','body','recipient_type','reporting_period','question_id'}:item[key]=value
            elif key in {'has_attachments','is_internal','is_suppressed'}:item[key]=value=='true'
            elif key=='sent_at':item[key]=datetime.fromisoformat(value)
            elif key in {'start_date','end_date'}:item[key]=date.fromisoformat(value)
            elif key in {'mean_score','top_box_pct','benchmark_pct'}:item[key]=float(value)
            else:item[key]=int(value)
        converted.append(item)
    return converted


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email-dir',type=Path,default=ROOT/'local-fixtures/emails')
    parser.add_argument('--q12-dir',type=Path,default=ROOT/'local-fixtures/q12')
    parser.add_argument('--apply',action='store_true',help='Execute the separately approved additive import and reviewed question corrections.')
    args=parser.parse_args()
    data=validate_files(args.email_dir,args.q12_dir)
    url=make_url(Settings.from_environment().database_url.get_secret_value()).set(drivername='postgresql+psycopg')
    options='-c lock_timeout=3000 -c statement_timeout=30000'
    if not args.apply:options+=' -c default_transaction_read_only=on'
    engine=create_engine(url,hide_parameters=True,connect_args={'connect_timeout':3,'options':options})
    with engine.begin() as c:
        if args.apply:
            c.execute(text('LOCK TABLE public.employees,public.email_accounts,public.employee_goals,public.project_tasks,public.employee_training,public.q12_groups IN SHARE MODE'))
            c.execute(text('LOCK TABLE public.q12_questions,public.q12_surveys,public.q12_results,public.email_records,public.email_recipients IN SHARE ROW EXCLUSIVE MODE'))
        else:assert c.execute(text('SHOW transaction_read_only')).scalar_one()=='on'
        corrections=check_database(c,data)
        if args.apply:
            for correction in corrections:
                c.execute(text('UPDATE public.q12_questions SET text=:text WHERE id=:id'),correction)
            for table,key in [('q12_surveys','surveys'),('q12_results','results'),('email_records','emails'),('email_recipients','recipients')]:
                rows=convert(data[key],key)
                columns=list(rows[0])
                statement=text(f"INSERT INTO public.{table} ({', '.join(columns)}) VALUES ({', '.join(':'+col for col in columns)})")
                for start in range(0,len(rows),500):c.execute(statement,rows[start:start+500])
                assert c.execute(text('SELECT count(*) FROM public.'+table)).scalar_one()==len(rows)
    engine.dispose()
    report={'status':'imported' if args.apply else 'preflight_only','question_text_corrections':len(corrections),
            'email_records':len(data['emails']),'email_recipients':len(data['recipients']),
            'q12_surveys':len(data['surveys']),'q12_results':len(data['results'])}
    (args.email_dir/('import-report.json' if args.apply else 'preflight-report.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':
    try:main()
    except Exception as error:
        raise SystemExit('Fixture import/preflight failed ('+type(error).__name__+'); verify destination counts before any retry.') from None
