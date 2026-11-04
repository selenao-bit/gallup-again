"""Infrastructure-only HTTP endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from .database import Database, DatabaseUnavailable


router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


def get_database(request: Request) -> Database:
    return request.app.state.database


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/health/db", response_model=HealthResponse, responses={503: {"description": "Database unavailable"}})
def database_health(database: Annotated[Database, Depends(get_database)]) -> HealthResponse:
    try:
        database.check()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return HealthResponse()
