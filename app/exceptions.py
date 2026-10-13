class AppError(Exception):
    """Base class for all expected, business-level errors."""

    status_code = 500
    code = "app_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class StudentNotFoundError(AppError):
    status_code = 404
    code = "student_not_found"

    def __init__(self, student_id: int) -> None:
        self.student_id = student_id
        super().__init__(f"Student with id {student_id} not found")


class DuplicateEmailError(AppError):
    status_code = 409
    code = "duplicate_email"

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__("A student with this email already exists")


class EmptyUpdateError(AppError):
    status_code = 422
    code = "empty_update"

    def __init__(self) -> None:
        super().__init__("No fields provided to update")

class ReportNotFoundError(AppError):
    status_code = 404
    code = "report_not_found"

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Report job {job_id} not found (it may have expired)")


class QueueUnavailableError(AppError):
    status_code = 503
    code = "queue_unavailable"

    def __init__(self) -> None:
        super().__init__("The job queue is temporarily unavailable")