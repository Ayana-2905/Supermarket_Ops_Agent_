from app.infrastructure.database.database import SessionLocal

from app.infrastructure.database.models import Product

from app.domain.billing.schemas import (
    CreateBillRequest,
    BillItemRequest
)

from app.domain.billing.service import BillingService


db = SessionLocal()

try:

    service = BillingService(db)

    request = CreateBillRequest(
        items=[
            BillItemRequest(
                product_id=2,
                quantity=2
            )
        ],
        idempotency_key="FINALIZE-IDEMPOTENCY-001"
    )

    bill = service.create_draft_bill(request)

    maggi = db.get(Product, 2)

    print("\n========== BEFORE ==========")
    print("Bill:", bill.bill_number)
    print("Status:", bill.status)
    print("Maggi stock:", maggi.quantity)

    # First finalization
    finalized_bill = service.finalize_bill(
        bill.bill_number,
        "UPI",
        "UPI-DEMO-001"
    )

    print("\n========== FIRST FINALIZATION ==========")
    print("Status:", finalized_bill.status)
    print("Payment:", finalized_bill.payment_mode)
    print("Reference:", finalized_bill.payment_reference)
    print("Maggi stock:", maggi.quantity)

    # Second finalization
    finalized_again = service.finalize_bill(
        bill.bill_number,
        "UPI",
        "UPI-DEMO-001"
    )

    print("\n========== SECOND FINALIZATION ==========")
    print("Status:", finalized_again.status)
    print("Maggi stock:", maggi.quantity)

finally:
    db.close()