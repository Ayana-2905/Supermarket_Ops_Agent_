import json

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.models import AgentEvent


def record_agent_event(
    event_type: str,
    status: str,
    tool_name: str | None = None,
    arguments: dict | None = None,
    result: object | None = None,
    telegram_update_id: str | None = None,
    conversation_id: str | None = None
):
    db = SessionLocal()

    try:
        event = AgentEvent(
            telegram_update_id=telegram_update_id,
            conversation_id=conversation_id,
            event_type=event_type,
            tool_name=tool_name,
            arguments=(
                json.dumps(arguments, default=str)
                if arguments is not None
                else None
            ),
            result=(
                json.dumps(result, default=str)
                if result is not None
                else None
            ),
            status=status
        )

        db.add(event)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Audit logging failed: {e}")

    finally:
        db.close()