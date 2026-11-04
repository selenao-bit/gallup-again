"""Bound prompt size and give each retrieved source category a turn in selection."""
import json
from collections import defaultdict, deque

MAX_CONTEXT_CHARS = 12000


def pack_context(records, gaps):
    categories = defaultdict(deque)
    for record in records:
        item = record.model_dump(mode='json')
        item['title'] = item['title'][:300]
        item['fields'] = {k:v[:1200] if isinstance(v,str) else v for k,v in item['fields'].items()}
        if record.category == 'engagement':
            # The statement is already the title. Preserve measured fields and scope;
            # UI source details still retain the original record projection.
            item['fields'] = {k:v for k,v in item['fields'].items() if k not in {'text','element','engagement_need'}}
        categories[record.category].append((record,item))
    context = {'records':[],'gaps':list(gaps)}
    selected = []
    def size():
        return len(json.dumps(context,ensure_ascii=False,separators=(',',':')))
    while any(categories.values()):
        for queue in categories.values():
            if not queue:continue
            original,item = queue.popleft()
            context['records'].append(item)
            if size() <= MAX_CONTEXT_CHARS - 300:
                selected.append(original)
            else:
                context['records'].pop()
    if len(selected) < len(records):
        context['gaps'].append(f'AI context includes {len(selected)} of {len(records)} retrieved records because of the prompt-size limit; omitted records were not reviewed.')
    if size() > MAX_CONTEXT_CHARS:
        raise ValueError('Context metadata exceeds prompt budget')
    return context,selected
