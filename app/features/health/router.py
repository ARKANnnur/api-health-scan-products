from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

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
async def readyz(db: DBDep) -> JSONResponse | ReadinessResponse:  
    db_ok = await check_database(db)
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "down"},
        )
    return ReadinessResponse(status="ready", database="up")