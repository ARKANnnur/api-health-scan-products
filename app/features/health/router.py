from fastapi import APIRouter, status

from app.core.exceptions import DatabaseError
from app.features.health.schemas import HealthResponse, ReadinessResponse
from app.features.health.service import check_database
from app.shared.deps import DBDep

router = APIRouter(prefix="/api/v1", tags=["health"])

VERSION = "1.0.0"


@router.get(
    "/healthz",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe (independen DB)",
)
async def healthz() -> HealthResponse:
    return HealthResponse(status="healthy", version=VERSION)


@router.get(
    "/readyz",
    response_model=ReadinessResponse,
    summary="Readiness probe (cek DB)",
    responses={
        200: {"description": "DB up"},
        503: {"description": "DB down"},
    },
)
async def readyz(db: DBDep) -> ReadinessResponse:
    db_ok = await check_database(db)
    if not db_ok:
        raise DatabaseError(message="Database is not ready")
    return ReadinessResponse(status="ready", database="up")
