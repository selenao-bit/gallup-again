"""Two bounded live smoke requests through the running app. Never reads API keys."""
import json
from time import perf_counter
import urllib.error
import urllib.request

BASE='http://127.0.0.1:5173/api'


def request(path, actor=None, question=None):
    headers={} if actor is None else {'X-Demo-Employee-Id':str(actor)}
    data=None
    if question is not None:
        headers['Content-Type']='application/json'
        data=json.dumps({'question':question}).encode()
    req=urllib.request.Request(BASE+path,headers=headers,data=data)
    try:
        with urllib.request.urlopen(req,timeout=40) as response:return json.load(response)
    except urllib.error.HTTPError as error:
        # Don't expose headers, settings, provider errors or response narratives.
        print('App request failed:',path,'HTTP',error.code)
        raise SystemExit(1) from None


def verify(label,result):
    assert result['mode'] in {'openai','azure'}
    assert result['content']['answer'].strip()
    citations=set(result['content']['cited_record_ids'])
    known={source['record_id'] for source in result['sources']}
    assert citations and citations==known
    categories={source['category'] for source in result['sources']}
    assert {'email','engagement'}<=categories,(label,'expected both requested source categories')
    print(label+': PASS; live answer characters='+str(len(result['content']['answer']))+
          '; cited sources='+str(len(citations))+'; categories='+','.join(sorted(categories)))


catalog=request('/demo/personas')
assert catalog['assistant_mode'] in {'openai','azure'} and catalog['assistant_available']
employee=next(p for p in catalog['personas'] if p['role']=='employee')
manager=next(p for p in catalog['personas'] if p['role']=='manager')
started=perf_counter()
result=request('/employee/chat',employee['employee_id'],
    'Summarize my recent synthetic emails and suggest one discussion topic from permitted Q12 group results. Cite at least one email and one Q12 result. Keep group engagement separate from individual performance; be concise.')
verify('Employee email + Q12',result)
print(f'Employee request elapsed: {perf_counter()-started:.2f}s')
reports=request('/manager/reports',manager['employee_id'])['reports']
assert reports
subject=reports[0]['employee_id']
started=perf_counter()
result=request(f'/manager/reports/{subject}/conversation',manager['employee_id'],
    'Summarize our shared synthetic training emails and suggest one discussion topic from permitted Q12 group results. Cite at least one email and one Q12 result. Explain the group scope and do not assess individual engagement. Be concise.')
verify('Manager shared email + Q12',result)
print(f'Manager request elapsed: {perf_counter()-started:.2f}s')
print('Verified live AI through frontend proxy; no keys or answer narratives printed.')
