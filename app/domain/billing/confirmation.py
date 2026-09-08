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
        print(
            f"[CONFIRMATION] SET pending: "
            f"chat_id={chat_id}, bill={bill_number}"
        )

        self.pending_bills[chat_id] = PendingBill(
            bill_number=bill_number,
            created_at=datetime.utcnow()
        )

        print(
            f"[CONFIRMATION] Current pending bills: "
            f"{self.pending_bills}"
        )

    def get_pending(
        self,
        chat_id: str
    ):
        print(
            f"[CONFIRMATION] GET pending: "
            f"chat_id={chat_id}"
        )

        print(
            f"[CONFIRMATION] Available chat IDs: "
            f"{list(self.pending_bills.keys())}"
        )

        pending = self.pending_bills.get(chat_id)

        if not pending:
            print(
                "[CONFIRMATION] NO PENDING BILL"
            )
            return None

        if (
            datetime.utcnow() - pending.created_at
            > timedelta(minutes=10)
        ):
            print(
                "[CONFIRMATION] Pending bill expired"
            )

            self.pending_bills.pop(
                chat_id,
                None
            )

            return None

        print(
            f"[CONFIRMATION] FOUND bill: "
            f"{pending.bill_number}"
        )

        return pending

    def clear(
        self,
        chat_id: str
    ):
        print(
            f"[CONFIRMATION] CLEAR chat_id={chat_id}"
        )

        self.pending_bills.pop(
            chat_id,
            None
        )