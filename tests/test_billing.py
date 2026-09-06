from app.infrastructure.database.database import SessionLocal

from app.domain.billing.schemas import (
    CreateBillRequest,
    BillItemRequest
)

from app.domain.billing.service import BillingService


db = SessionLocal()

try:

    request = CreateBillRequest(
        items=[
            BillItemRequest(
                product_id=2,
                quantity=2
            ),
            BillItemRequest(
                product_id=5,
                quantity=1
            )
        ],
        idempotency_key="TEST-BILL-001"
    )

    service = BillingService(db)

    bill = service.create_draft_bill(request)

    print("\n========== DRAFT BILL ==========")
    print(f"Bill Number : {bill.bill_number}")
    print(f"Status      : {bill.status}")
    print(f"Subtotal    : ₹{bill.subtotal}")
    print(f"CGST        : ₹{bill.cgst}")
    print(f"SGST        : ₹{bill.sgst}")
    print(f"TOTAL       : ₹{bill.total}")
    print("================================")

finally:
    db.close()