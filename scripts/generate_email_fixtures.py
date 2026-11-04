"""Generate deterministic synthetic internal emails from existing work records.

Only SELECTs are issued. Output is local and is never imported by this script.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy import text
from app.config import Settings
from app.database import Database

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = datetime(2026, 9, 30, 12)
RECORD_COLUMNS = ['email_id','thread_id','sender_id','sent_at','subject','body','reply_to_id','has_attachments','is_internal']
RECIPIENT_COLUMNS = ['email_id','recipient_id','recipient_type']


def build(employees, sources):
    """Two-message discussion threads; work facts are copied, not inferred."""
    people = {r['employee_id']: r for r in employees}
    records, recipients, anchors = [], [], []
    templates = {
        'goal': ('Goal check-in', 'Could we review the next steps and any support you need?'),
        'task': ('Project task check-in', 'Could we discuss the recorded work and any open questions?'),
        'training': ('Learning and development check-in', 'Could we discuss how this learning connects to your work?'),
    }
    for source in sorted(sources, key=lambda r:(r['employee_id'],r['category'],r['source_id'])):
        person = people.get(source['employee_id'])
        if person is None or person['employment_status'] not in {'Active','Leave'}:
            continue
        manager = people.get(person['supervisor_id'])
        if not manager or manager['employee_id']==person['employee_id'] or manager['employment_status'] not in {'Active','Leave'}:
            continue
        source_time = source['record_date']
        if isinstance(source_time,str):source_time=datetime.fromisoformat(source_time)
        if source_time and not isinstance(source_time,datetime):source_time=datetime.combine(source_time,datetime.min.time())
        first = max(person['hire_date'], manager['hire_date'], source_time or person['hire_date'])
        if first > SNAPSHOT:continue
        first = min(first + timedelta(days=1), SNAPSHOT - timedelta(hours=2))
        if first < max(person['hire_date'],manager['hire_date'],source_time or person['hire_date']):continue
        first = first.replace(microsecond=0)
        title, prompt=templates[source['category']]
        reference=f"{source['source_table']}:{source['source_id']}"
        thread = len(anchors)+1
        first_id=len(records)+1
        subject=f"[Synthetic demo] {title}: {source['title']}"
        body=(f"[Synthetic email fixture; not an actual communication.]\n\n"
              f"For our next work discussion, the source record {reference} lists:\n"
              f"{source['title']}\nRecorded status at the demo snapshot: {source['status'] or 'Not recorded'}.\n\n"
              f"{prompt}\n\nThis message is simulated as of the September 2026 snapshot. "
              "Its message date is illustrative, not evidence of when that status was reached.")
        records.append(dict(zip(RECORD_COLUMNS,[first_id,thread,manager['employee_id'],first.isoformat(),subject,body,'','false','true'])))
        recipients.append({'email_id':first_id,'recipient_id':person['employee_id'],'recipient_type':'to'})
        reply_id=first_id+1
        reply=("[Synthetic email fixture; not an actual communication.]\n\n"
               "Thanks for raising this. I would like to discuss the record, my perspective, "
               "and what support or clarification would help. Please use the source record "
               f"{reference} for its recorded details. This simulated reply does not assert a new outcome or commitment.")
        records.append(dict(zip(RECORD_COLUMNS,[reply_id,thread,person['employee_id'],(first+timedelta(hours=1)).isoformat(),'Re: '+subject,reply,first_id,'false','true'])))
        recipients.append({'email_id':reply_id,'recipient_id':manager['employee_id'],'recipient_type':'to'})
        anchors.append({'thread_id':thread,'employee_id':person['employee_id'],'supervisor_id':manager['employee_id'],
                        'source_record_id':reference,'source_title':source['title'],'source_status':source['status'],
                        'source_date':source_time.isoformat() if source_time else None})
    return records, recipients, anchors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'local-fixtures/emails')
    args=parser.parse_args()
    with Database(Settings.from_environment()).read() as c:
        assert c.execute(text('SHOW transaction_read_only')).scalar_one()=='on'
        schema={t:[r for r in c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"),{'t':t}).scalars()] for t in ['email_records','email_recipients']}
        assert schema['email_records']==RECORD_COLUMNS
        assert schema['email_recipients']==RECIPIENT_COLUMNS
        counts={t:c.execute(text('SELECT count(*) FROM public.'+t)).scalar_one() for t in schema}
        assert not any(counts.values()), 'Email destinations must be empty; existing rows will not be replaced.'
        employees=[dict(r) for r in c.execute(text('''SELECT e.employee_id,e.supervisor_id,e.employment_status,e.hire_date
            FROM public.employees e WHERE EXISTS (SELECT 1 FROM public.email_accounts a WHERE a.employee_id=e.employee_id)
            ORDER BY e.employee_id''')).mappings()]
        sources=[]
        for category,table,key,title,status,date in [
            ('goal','employee_goals','goal_id','goal_description','complete_status','start_date'),
            ('task','project_tasks','task_id','title','task_status','created_date'),
            ('training','employee_training','training_id','program_name','completion_status','assigned_date')]:
            rows=c.execute(text(f'''SELECT DISTINCT ON (employee_id) employee_id,{key} AS source_id,
                {title} AS title,{status} AS status,{date} AS record_date FROM public.{table}
                WHERE {date}<=:snapshot ORDER BY employee_id,{date} DESC NULLS LAST,{key} DESC'''),{'snapshot':SNAPSHOT}).mappings()
            sources.extend({**dict(r),'category':category,'source_table':table} for r in rows)
    records,recipients,anchors=build(employees,sources)
    assert records and len(records)==len(recipients)==2*len(anchors)
    files={}
    for name,columns,rows in [('email_records.csv',RECORD_COLUMNS,records),('email_recipients.csv',RECIPIENT_COLUMNS,recipients)]:
        import io
        buffer=io.StringIO(newline='')
        writer=csv.DictWriter(buffer,fieldnames=columns,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        files[name]=buffer.getvalue().encode()
    files['source_anchors.json']=(json.dumps(anchors,indent=2,default=str)+'\n').encode()
    manifest={'status':'generated_not_imported','snapshot':SNAPSHOT.isoformat(),'records':len(records),'recipients':len(recipients),
              'threads':len(anchors),'employees_with_threads':len({a['employee_id'] for a in anchors}),
              'source_sha256':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()},
              'generation_policy':'Two clearly marked synthetic messages per existing latest goal/task/training source, between employee and current supervisor. No new outcomes or commitments; no attachments or external recipients.'}
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    args.output.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():
        p=args.output/name
        if p.exists() and p.read_bytes()!=data:raise ValueError('Refusing to overwrite differing generated output.')
    for name,data in files.items():(args.output/name).write_bytes(data)
    print('Generated',len(records),'synthetic messages in',len(anchors),'threads for',manifest['employees_with_threads'],'employees. Database writes: NONE.')

if __name__=='__main__':
    try:main()
    except Exception as error:
        raise SystemExit('Email fixture generation failed ('+type(error).__name__+'); no database writes attempted.') from None
