import json
from datetime import datetime, timedelta
from fastapi import Header, HTTPException
from sqlalchemy.orm import Session
from app.models import IdempotencyKey


IDEMPOTENCY_TTL_HOURS = 24


def get_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://httpstatuses.com/400",
                "title": "Bad Request",
                "status": 400,
                "detail": "Idempotency-Key header is required",
            },
        )
    return idempotency_key


def check_idempotency(key: str, db: Session) -> IdempotencyKey | None:
    record = db.get(IdempotencyKey, key)
    if record is None:
        return None
    cutoff = datetime.utcnow() - timedelta(hours=IDEMPOTENCY_TTL_HOURS)
    if record.created_at < cutoff:
        db.delete(record)
        db.commit()
        return None
    return record


def store_idempotency(key: str, response_body: str, status_code: int, db: Session) -> None:
    record = IdempotencyKey(key=key, response_body=response_body, status_code=status_code)
    db.add(record)
    db.commit()
