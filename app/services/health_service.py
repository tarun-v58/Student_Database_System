import logging
import time
from collections.abc import Callable

from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import CheckResult, ReadinessReport

logger = logging.getLogger("app.health")


def _timed(name: str, probe: Callable[[], object]) -> CheckResult:
    started = time.perf_counter()
    try:
        probe()
        ok = True
    except Exception as exc:  # a probe must never raise: any error means "fail"
        # Log the error type only: messages can contain hosts or credentials.
        logger.warning("Health check %s failed: %s", name, type(exc).__name__)
        ok = False
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    return CheckResult(status="ok" if ok else "fail", latency_ms=latency_ms)


class HealthService:
    def __init__(self, db: Session, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    def check_database(self) -> CheckResult:
        return _timed("database", lambda: self.db.execute(text("SELECT 1")))

    def check_redis(self) -> CheckResult:
        return _timed("redis", self.redis.ping)

    def readiness(self) -> ReadinessReport:
        database = self.check_database()
        redis = self.check_redis()
        if database.status == "fail":
            status = "unavailable"
        elif redis.status == "fail":
            status = "degraded"
        else:
            status = "ok"
        return ReadinessReport(
            status=status, checks={"database": database, "redis": redis}
        )