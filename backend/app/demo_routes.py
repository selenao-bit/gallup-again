"""Demo transport validation; policy, retrieval and AI remain separate."""
import re
from fastapi import APIRouter, Depends, Request
from .demo_models import ChatAnswer, ChatRequest, CurrentPersona, Dashboard, PersonaList, ReportPage
from .services.access import DemoError

router = APIRouter(dependencies=[])

def enabled(request: Request):
    if not request.app.state.settings.demo_identity_enabled:
        raise DemoError(404, 'not_found', 'Demo feature unavailable.')

def actor(request: Request, _=Depends(enabled)):
    values = request.headers.getlist('x-demo-employee-id')
    if not values:
        raise DemoError(401, 'demo_selection_required', 'Select a demo persona.')
    if len(values)!=1 or len(values[0]) > 11 or not re.fullmatch(r'0|-?[1-9][0-9]*', values[0]) or not -2147483648 <= int(values[0]) <= 2147483647:
        raise DemoError(422, 'invalid_demo_request', 'Invalid demo selection.')
    resolved = request.app.state.workspace_service.resolve(int(values[0]))
    request.state.demo_actor_id = resolved[0].employee_id
    return resolved

def no_query(request: Request):
    if request.query_params:
        raise DemoError(422, 'invalid_demo_request', 'Unsupported query parameter.')

@router.get('/demo/personas', response_model=PersonaList, dependencies=[Depends(enabled), Depends(no_query)])
def personas(request: Request):
    return request.app.state.workspace_service.personas()

@router.get('/demo/me', response_model=CurrentPersona, dependencies=[Depends(no_query)])
def me(resolved=Depends(actor)):
    return resolved[1]

@router.get('/manager/reports', response_model=ReportPage)
def reports(request: Request, resolved=Depends(actor)):
    params = request.query_params
    if set(params)-{'limit', 'after_employee_id'} or any(len(params.getlist(k))>1 for k in params):
        raise DemoError(422, 'invalid_demo_request', 'Unsupported or duplicate query parameter.')
    try:
        limit = int(params.get('limit','50'))
        after = int(params['after_employee_id']) if 'after_employee_id' in params else None
        if not 1 <= limit <= 100 or (after is not None and not -2147483648 <= after <= 2147483647):
            raise ValueError
    except ValueError:
        raise DemoError(422, 'invalid_demo_request', 'Invalid report page parameters.') from None
    return request.app.state.demo_service.reports(resolved[0], limit, after)

@router.get('/manager/reports/{employee_id}/dashboard', response_model=Dashboard, dependencies=[Depends(no_query)])
def dashboard(employee_id: int, request: Request, resolved=Depends(actor)):
    return request.app.state.demo_service.overview(resolved[0], employee_id)

@router.post('/manager/reports/{employee_id}/chat', response_model=ChatAnswer, dependencies=[Depends(no_query)])
def chat(employee_id: int, body: ChatRequest, request: Request, resolved=Depends(actor)):
    return request.app.state.assistant.answer(resolved[0], employee_id, body.question)
