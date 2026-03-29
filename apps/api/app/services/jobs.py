from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import JobRecord, JobStatus, User
from app.workers.queue import get_queue


def enqueue_model_retrain(db: Session, requested_by: User | None) -> JobRecord:
    record = JobRecord(job_type="model_retrain", status=JobStatus.QUEUED, requested_by_id=requested_by.id if requested_by else None)
    db.add(record)
    db.commit()
    db.refresh(record)

    queue = get_queue()
    queue.enqueue("app.workers.tasks.run_retrain_job", record.id, job_id=record.id)
    return record
