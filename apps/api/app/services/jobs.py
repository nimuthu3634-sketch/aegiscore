from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import JobRecord, JobStatus, User
from app.services.audit import record_audit
from app.workers.queue import get_queue


class JobQueueUnavailableError(RuntimeError):
    """Raised when a background job cannot be queued."""


def enqueue_model_retrain(db: Session, requested_by: User | None) -> JobRecord:
    record = JobRecord(job_type="model_retrain", status=JobStatus.QUEUED, requested_by_id=requested_by.id if requested_by else None)
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        queue = get_queue()
        queue.enqueue("app.workers.tasks.run_retrain_job", record.id, job_id=record.id)
    except Exception as exc:
        record.status = JobStatus.FAILED
        record.error_message = "Redis-backed background processing is unavailable. Start Redis and the worker before retrying model retraining."
        db.commit()
        db.refresh(record)
        record_audit(
            db,
            actor=requested_by,
            action="ml.retrain_queue_unavailable",
            entity_type="job",
            entity_id=record.id,
            details={"job_id": record.id, "job_type": "model_retrain", "error": str(exc)},
        )
        raise JobQueueUnavailableError(record.error_message) from exc

    record_audit(
        db,
        actor=requested_by,
        action="ml.retrain_queued",
        entity_type="job",
        entity_id=record.id,
        details={"job_id": record.id, "job_type": "model_retrain"},
    )
    return record
