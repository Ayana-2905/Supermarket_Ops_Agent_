from datetime import datetime, timedelta

from app.domain.billing.state import PendingBill


class ConfirmationManager:

    def __init__(self):
        self.pending_bill: PendingBill | None = None

    def set_pending(self, bill_number: str):
        self.pending_bill = PendingBill(
            bill_number=bill_number,
            created_at=datetime.utcnow()
        )

    def get_pending(self):
        if not self.pending_bill:
            return None

        # Expire confirmation after 10 minutes
        if datetime.utcnow() - self.pending_bill.created_at > timedelta(
            minutes=10
        ):
            self.pending_bill = None
            return None

        return self.pending_bill

    def clear(self):
        self.pending_bill = None