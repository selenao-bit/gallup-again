"""Application factory. Startup validates configuration without connecting to PostgreSQL."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timezone

from .config import Settings
from .database import Database
from .routes import router
from .demo_routes import router as demo_router
from .repositories.demo import DemoRepository
from .services.demo import DemoService
from .services.access import DemoError
from .ai.assistant import Assistant
from .database import DatabaseUnavailable
from .repositories.workspace import WorkspaceRepository
from .services.workspace import WorkspaceService
from .ai.workspace import WorkspaceAssistant
from .workspace_routes import router as workspace_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_environment()
    database = Database(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            database.close()

    app = FastAPI(
        title="Performance Review Assistant", lifespan=lifespan,
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.state.database = database
    app.state.settings = settings
    app.state.demo_service = DemoService(DemoRepository(database), settings)
    app.state.assistant = Assistant(app.state.demo_service, settings)
    app.state.workspace_repository = WorkspaceRepository(database)
    app.state.workspace_service = WorkspaceService(app.state.workspace_repository, settings)
    app.state.workspace_assistant = WorkspaceAssistant(app.state.workspace_repository, settings)

    @app.middleware('http')
    async def demo_metadata(request, call_next):
        is_demo = request.url.path.startswith(('/demo/', '/manager/', '/employee/'))
        if is_demo and not settings.demo_identity_enabled:
            return JSONResponse(status_code=404, headers={'Cache-Control': 'no-store'}, content={'detail': {'code': 'not_found', 'message': 'Demo feature unavailable.'}})
        response = await call_next(request)
        if is_demo:
            response.headers['Cache-Control'] = 'no-store'
            if settings.demo_diagnostics:
                # No raw headers, questions, records or secrets; best-effort only.
                action = ('chat' if request.url.path.endswith('/chat') else
                          'overview' if request.url.path.endswith('/dashboard') else 'identity_or_reports')
                logging.getLogger('uvicorn.error').info(
                    'demo_metadata time=%s actor=%s action=%s status=%s',
                    datetime.now(timezone.utc).isoformat(),
                    getattr(request.state, 'demo_actor_id', None), action, response.status_code)
        return response

    @app.exception_handler(DemoError)
    async def demo_error(request, error):
        return JSONResponse(status_code=error.status, content={'detail': {'code': error.code, 'message': error.message}})

    @app.exception_handler(DatabaseUnavailable)
    async def data_error(request, error):
        return JSONResponse(status_code=503, content={'detail': {'code': 'data_unavailable', 'message': 'Corporate data is unavailable. Check the database connection and retry.'}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse(status_code=422, content={'detail': {'code': 'invalid_demo_request', 'message': 'Invalid request fields.'}})

    app.include_router(router)
    app.include_router(demo_router)
    app.include_router(workspace_router)
    return app
