from __future__ import annotations

from datetime import datetime, timezone

from rq import Worker

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.ml.scoring import train_model
from app.models.entities import JobRecord, JobStatus
from app.services.domain import rescore_alerts
from app.workers.queue import get_redis_connection


def run_retrain_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        record = db.query(JobRecord).filter(JobRecord.id == job_id).one()
        record.status = JobStatus.RUNNING
        record.started_at = datetime.now(timezone.utc)
        db.commit()

        metadata = train_model(db, version=f"{get_settings().model_version}-{job_id[:8]}")
        recalc_result = rescore_alerts(db, open_only=False)
        record.status = JobStatus.SUCCEEDED
        record.completed_at = datetime.now(timezone.utc)
        record.result = {"model_version": metadata.version, "metrics": metadata.metrics, "rescored_alerts": recalc_result}
        db.commit()
    except Exception as error:  # pragma: no cover
        record = db.query(JobRecord).filter(JobRecord.id == job_id).one_or_none()
        if record is not None:
            record.status = JobStatus.FAILED
            record.completed_at = datetime.now(timezone.utc)
            record.error_message = str(error)
            db.commit()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    redis_connection = get_redis_connection()
    Worker(["ml"], connection=redis_connection).work()
