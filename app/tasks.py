import logging
import time

logger = logging.getLogger("app.tasks")


def write_audit_log(action: str, student_id: int) -> None:
    logger.info("AUDIT action=%s student_id=%s", action, student_id)


def send_welcome_email(student_id: int, name: str, email: str) -> None:
    logger.info("Sending welcome email for student %s", student_id)
    time.sleep(3)  # pretend the mail server is slow
    logger.info("Welcome email sent for student %s", student_id)