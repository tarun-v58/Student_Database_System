from fastapi import APIRouter, Response, status

from app.dependencies import HealthServiceDep
from app.schemas import CheckResult, ReadinessReport

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def liveness():
    return {"status": "ok"}


@router.get(
    "/db",
    response_model=CheckResult,
    responses={503: {"description": "Database unreachable"}},
)
def database_health(response: Response, service: HealthServiceDep):
    result = service.check_database()
    if result.status == "fail":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get(
    "/ready",
    response_model=ReadinessReport,
    responses={503: {"description": "Not ready to serve traffic"}},
)
def readiness(response: Response, service: HealthServiceDep):
    report = service.readiness()
    if report.status == "unavailable":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report