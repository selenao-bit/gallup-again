"""Employee APIs accept no client-selected employee scope."""
from fastapi import APIRouter, Depends, Request, Query
from .demo_routes import actor, no_query
from .workspace_models import RecordBundle, WorkspaceQuestion, AnswerResult
from .services.access import require_manager, unavailable

router=APIRouter()

@router.get('/employee/record',response_model=RecordBundle,dependencies=[Depends(no_query)])
def record(request:Request,resolved=Depends(actor)):
    return request.app.state.workspace_repository.bundle(resolved[0],resolved[0].employee_id)

@router.get('/employee/emails')
def emails(request:Request,before:int|None=Query(default=None,ge=1),resolved=Depends(actor)):
    if set(request.query_params)-{'before'}:
        from .services.access import DemoError
        raise DemoError(422,'invalid_demo_request','Unsupported query parameter.')
    return request.app.state.workspace_repository.emails(resolved[0],before)

@router.get('/employee/engagement',dependencies=[Depends(no_query)])
def engagement(request:Request,resolved=Depends(actor)):
    return request.app.state.workspace_repository.engagement(resolved[0])

@router.post('/employee/chat',response_model=AnswerResult,dependencies=[Depends(no_query)])
def chat(body:WorkspaceQuestion,request:Request,resolved=Depends(actor)):
    return request.app.state.workspace_assistant.answer(resolved[0],resolved[0].employee_id,body.question)

@router.post('/employee/engagement/prepare',response_model=AnswerResult,dependencies=[Depends(no_query)])
def prepare(body:WorkspaceQuestion,request:Request,resolved=Depends(actor)):
    return request.app.state.workspace_assistant.answer(resolved[0],resolved[0].employee_id,body.question,engagement=True)

@router.get('/manager/reports/{employee_id}/record',response_model=RecordBundle,dependencies=[Depends(no_query)])
def manager_record(employee_id:int,request:Request,resolved=Depends(actor)):
    require_manager(resolved[0])
    if employee_id == resolved[0].employee_id:
        raise unavailable()
    return request.app.state.workspace_repository.bundle(resolved[0],employee_id)

@router.post('/manager/reports/{employee_id}/conversation',response_model=AnswerResult,dependencies=[Depends(no_query)])
def conversation(employee_id:int,body:WorkspaceQuestion,request:Request,resolved=Depends(actor)):
    require_manager(resolved[0])
    if employee_id == resolved[0].employee_id:
        raise unavailable()
    return request.app.state.workspace_assistant.answer(resolved[0],employee_id,body.question)
