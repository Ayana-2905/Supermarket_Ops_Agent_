from datetime import datetime, timedelta

from app.domain.billing.state import PendingBill

class ConfirmationManager:

    def __init__(self):
        self.pending_bills = {}

    def set_pending(
        self,
        chat_id: str,
        bill_number: str
    ):
        self.pending_bills[chat_id] = PendingBill(
            bill_number=bill_number,
            created_at=datetime.utcnow()
        )

    def get_pending(
        self,
        chat_id: str
    ):
        pending = self.pending_bills.get(chat_id)

        if not pending:
            return None

        if (
            datetime.utcnow() - pending.created_at
            > timedelta(minutes=10)
        ):
            self.pending_bills.pop(
                chat_id,
                None
            )
            return None

        return pending

    def clear(
        self,
        chat_id: str
    ):
        self.pending_bills.pop(
            chat_id,
            None
        )