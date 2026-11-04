"""Purpose-specific, deterministic retrieval. No model-selected scopes or SQL."""
import re
from ..workspace_models import Record

STOP_WORDS = set('what which when where who how why can could would should please tell show give help about with from have has had does did this that these those them they their there your you our and the for are was were will my me i of to in on is it a an email emails message messages mail inbox sent send received receive manager employee records record explain summarize summary prepare conversation discuss discussion'.split())
EMAIL_WORDS = {'email','emails','mail','message','messages','inbox','correspondence'}
Q12_WORDS = {'q12','engagement','survey','surveys','pulse','team engagement','state of the team'}
CATEGORY_WORDS = {
    'goals': {'goal','goals','okr','okrs'},
    'tasks': {'task','tasks','project','projects','late','revisions'},
    'training': {'training','course','courses','certification','learning'},
    'reviews': {'review','reviews','rating','ratings'},
    'self_assessments': {'self-assessment','self-assessments','reflection','reflections','aspirations'},
}


def terms_for(question):
    return list(dict.fromkeys(w for w in re.findall(r'[a-z0-9]+',question.lower()) if len(w)>2 and w not in STOP_WORDS))[:8]


def retrieve(repository, actor, subject_id, question, engagement=False, bundle=None):
    # This independently rechecks the employee/direct-report boundary before any retrieval.
    bundle = repository.bundle(actor, subject_id) if bundle is None else bundle
    words = set(re.findall(r'[a-z0-9-]+',question.lower()))
    want_email = bool(words & EMAIL_WORDS)
    want_q12 = engagement or bool(words & Q12_WORDS) or 'state of the team' in question.lower()
    categories = {category for category, aliases in CATEGORY_WORDS.items() if words & aliases}
    context_only = (want_email or want_q12) and not categories
    terms = terms_for(question)
    candidates = [] if context_only else [r for r in bundle.records if not categories or r.category in categories]
    def relevance(record):
        haystack = (record.title+' '+' '.join(str(v) for v in record.fields.values())).lower()
        return (sum(term in haystack for term in terms), record.date or '', record.record_id)
    records = sorted(candidates,key=relevance,reverse=True)[:60]
    gaps = list(bundle.gaps)
    if want_email:
        email_terms = [w for w in terms if w not in {'says','say','saying','talk','talked','find','recent','latest','last'}]
        messages = repository.email_context(actor,subject_id,email_terms)
        records.extend(messages)
        gaps.append('Email retrieval includes at most 12 matching messages this persona sent or received; a manager view additionally requires the direct report to participate. Message bodies are truncated to 1,200 characters for AI. Dates and wording are synthetic, not observed communications.')
        if not messages:gaps.append('No permitted email messages matched this question; other inboxes were not searched.')
    if want_q12:
        data = repository.engagement(actor,subject_id)
        names = {g['group_id']:g['group_name'] for g in data['groups']}
        periods = {s['survey_id']:s for s in data['surveys']}
        # Default to one relevant group and latest wave; explicit comparisons retain
        # up to two waves. Selection only narrows the already-authorized dataset.
        group_match = re.search(r'\bgroup\s+(\d+)\b',question,re.IGNORECASE)
        survey_match = re.search(r'\bsurvey\s+(\d+)\b',question,re.IGNORECASE)
        priority = {'Team':3,'Department':2,'Company':1}
        groups = sorted(data['groups'],key=lambda g:priority.get(g.get('group_type'),0),reverse=True)
        requested_types = {kind for word,kind in [('team','Team'),('department','Department'),('company','Company')] if word in words}
        if group_match:
            groups = [g for g in groups if g['group_id']==int(group_match.group(1))]
        elif requested_types:
            groups = [g for g in groups if g.get('group_type') in requested_types]
        else:
            groups = groups[:1]
        surveys = data['surveys']
        named_periods = [s for s in surveys if s['reporting_period'].lower() in question.lower()]
        if survey_match:
            surveys = [s for s in surveys if s['survey_id']==int(survey_match.group(1))]
        elif named_periods:
            surveys = named_periods[:2]
        else:
            compare = bool(words & {'compare','comparison','changed','change','changes','trend','trends','waves','both','across'})
            surveys = surveys[:2 if compare else 1]
        group_ids = [g['group_id'] for g in groups]
        survey_ids = [s['survey_id'] for s in surveys]
        results = [r for r in data['results'] if r['group_id'] in group_ids and r['survey_id'] in survey_ids]
        results.sort(key=lambda r:(group_ids.index(r['group_id']),survey_ids.index(r['survey_id'])))
        item_count = 0
        for result in results:
            if result['suppressed']:
                gaps.append(f"Group {result['group_id']}, survey {result['survey_id']}: results are suppressed or unavailable; no scores are provided.")
                continue
            if item_count + len(result['items']) > 36:
                gaps.append('Additional permitted Q12 group/wave results were omitted from the 36-item AI context limit.')
                break
            for item in result['items']:
                survey = periods[result['survey_id']]
                records.append(Record(record_id=f"q12_results:{result['survey_id']}:{result['group_id']}:{item['question_id']}",
                    category='engagement',title=item['text'],date=str(survey.get('end_date') or '') or None,
                    fields={**item,'group_name':names[result['group_id']],'group_id':result['group_id'],
                            'survey_id':result['survey_id'],'reporting_period':survey['reporting_period']}))
            item_count += len(result['items'])
        if groups and surveys:
            gaps.append('Q12 context covers '+', '.join(g['group_name'] for g in groups)+'; periods '+', '.join(s['reporting_period'] for s in surveys)+'. Other groups/periods were not included unless explicitly requested.')
        if not groups or not surveys:
            gaps.append('The requested Q12 group or wave is unavailable in the current permitted scope.')
        gaps.append('Q12 is synthetic group context using current memberships for simulated historical waves. Benchmarks are synthetic. Group patterns cannot establish an individual employee performance or cause.')
        if not data['surveys']:gaps.append('No Q12 survey waves are available.')
    if not records:gaps.append('No permitted source records were retrieved for this question.')
    return records,gaps
