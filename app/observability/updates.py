from sqlalchemy import select

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.models import ProcessedUpdate


def is_update_processed(update_id: str) -> bool:
    db = SessionLocal()

    try:
        existing = db.scalar(
            select(ProcessedUpdate).where(
                ProcessedUpdate.telegram_update_id == update_id
            )
        )

        return existing is not None

    finally:
        db.close()


def mark_update_processed(update_id: str) -> bool:
    db = SessionLocal()

    try:
        existing = db.scalar(
            select(ProcessedUpdate).where(
                ProcessedUpdate.telegram_update_id == update_id
            )
        )

        if existing:
            return False

        db.add(
            ProcessedUpdate(
                telegram_update_id=update_id
            )
        )

        db.commit()

        return True

    except Exception:
        db.rollback()
        return False

    finally:
        db.close()