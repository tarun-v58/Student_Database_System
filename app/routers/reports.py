from fastapi import APIRouter, status

from app.dependencies import ReportServiceDep
from app.schemas import ReportRequest, ReportStatus

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "",
    response_model=ReportStatus,
    status_code=status.HTTP_202_ACCEPTED,
    responses={503: {"description": "Job queue unavailable"}},
)
def request_report(service: ReportServiceDep, body: ReportRequest | None = None):
    department = body.department if body else None
    return service.request_report(department)


@router.get(
    "/{job_id}",
    response_model=ReportStatus,
    responses={
        404: {"description": "Report job not found or expired"},
        503: {"description": "Job queue unavailable"},
    },
)
def get_report(job_id: str, service: ReportServiceDep):
    return service.get_report(job_id)