"""Prompt bounds and source traceability independent of live model behavior."""
import json
from app.ai.context import pack_context,MAX_CONTEXT_CHARS
from app.workspace_models import Record


def test_context_budget_and_category_turns_preserve_actual_ids():
    records=[Record(record_id=f'{category}:{i}',category=category,title='Test',fields={'first':'x'*1200,'second':'y'*1200})
             for category in ['training','email','engagement'] for i in range(12)]
    context,selected=pack_context(records,[])
    assert len(json.dumps(context,ensure_ascii=False,separators=(',',':')))<=MAX_CONTEXT_CHARS
    assert len(selected)<len(records)
    assert {r.category for r in selected}=={'training','email','engagement'}
    assert {r.record_id for r in selected}=={r['record_id'] for r in context['records']}
    assert any('omitted records were not reviewed' in g for g in context['gaps'])


def test_engagement_drops_duplicate_text_but_preserves_scope_and_measurement():
    record=Record(record_id='q12_results:2:3:Q01',category='engagement',title='Expectations',fields={'text':'Expectations','element':'Basic Needs','mean_score':4.1,'group_name':'Team','survey_id':2,'group_id':3,'question_id':'Q01'})
    context,selected=pack_context([record],[])
    fields=context['records'][0]['fields']
    assert 'text' not in fields and fields['mean_score']==4.1 and fields['group_id']==3
    assert selected[0].fields['text']=='Expectations'
