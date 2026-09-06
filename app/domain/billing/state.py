from dataclasses import dataclass
from datetime import datetime


@dataclass
class PendingBill:
    bill_number: str
    created_at: datetime