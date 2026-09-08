from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    Product,
    Bill,
    BillItem
)


class BillingService:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # CALCULATE BILL
    # ---------------------------------------------------------

    def calculate_bill(self, request):

        if not request.items:
            raise ValueError(
                "BILL_MUST_HAVE_ITEMS"
            )

        bill_items = []

        subtotal = 0.0
        total_cgst = 0.0
        total_sgst = 0.0

        for item in request.items:

            product = self.db.get(
                Product,
                item.product_id
            )

            if not product:
                raise ValueError(
                    f"PRODUCT_NOT_FOUND:{item.product_id}"
                )

            if item.quantity <= 0:
                raise ValueError(
                    "QUANTITY_MUST_BE_POSITIVE"
                )

            if item.quantity > product.quantity:
                raise ValueError(
                    f"INSUFFICIENT_STOCK:{product.name}"
                )

            taxable_amount = (
                item.quantity *
                product.sell_price
            )

            gst_amount = (
                taxable_amount *
                product.gst_rate /
                100
            )

            cgst = gst_amount / 2
            sgst = gst_amount / 2

            line_total = (
                taxable_amount +
                cgst +
                sgst
            )

            subtotal += taxable_amount
            total_cgst += cgst
            total_sgst += sgst

            bill_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "quantity": item.quantity,
                "unit": product.unit,
                "unit_price": product.sell_price,
                "gst_rate": product.gst_rate,
                "taxable_amount": round(
                    taxable_amount,
                    2
                ),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "line_total": round(
                    line_total,
                    2
                )
            })

        total = (
            subtotal +
            total_cgst +
            total_sgst
        )

        return {
            "items": bill_items,
            "subtotal": round(subtotal, 2),
            "cgst": round(total_cgst, 2),
            "sgst": round(total_sgst, 2),
            "total": round(total, 2)
        }

    # ---------------------------------------------------------
    # CREATE DRAFT
    # ---------------------------------------------------------

    def create_draft_bill(self, request):

        if request.idempotency_key:

            existing_bill = self.db.scalar(
                select(Bill).where(
                    Bill.idempotency_key ==
                    request.idempotency_key
                )
            )

            if existing_bill:
                return existing_bill

        calculated = self.calculate_bill(
            request
        )

        bill_number = (
            f"BILL-"
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        bill = Bill(
            bill_number=bill_number,
            customer_id=request.customer_id,
            status="DRAFT",
            subtotal=calculated["subtotal"],
            cgst=calculated["cgst"],
            sgst=calculated["sgst"],
            total=calculated["total"],
            idempotency_key=request.idempotency_key
        )

        self.db.add(bill)
        self.db.flush()

        for item in calculated["items"]:

            self.db.add(
                BillItem(
                    bill_id=bill.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    gst_rate=item["gst_rate"],
                    taxable_amount=item["taxable_amount"],
                    cgst=item["cgst"],
                    sgst=item["sgst"],
                    line_total=item["line_total"]
                )
            )

        self.db.commit()
        self.db.refresh(bill)

        return bill

    # ---------------------------------------------------------
    # GET DRAFT
    # ---------------------------------------------------------

    def get_draft_bill(
        self,
        bill_number: str
    ):

        bill = self.db.scalar(
            select(Bill).where(
                Bill.bill_number ==
                bill_number
            )
        )

        if not bill:
            raise ValueError(
                "BILL_NOT_FOUND"
            )

        if bill.status != "DRAFT":
            raise ValueError(
                "BILL_NOT_DRAFT"
            )

        return bill

    # ---------------------------------------------------------
    # EDIT DRAFT
    # ---------------------------------------------------------

    def edit_draft_bill(
        self,
        bill_number: str,
        items
    ):

        bill = self.get_draft_bill(
            bill_number
        )

        request = type(
            "BillRequest",
            (),
            {
                "items": items
            }
        )()

        calculated = self.calculate_bill(
            request
        )

        bill.items.clear()

        for item in calculated["items"]:

            bill.items.append(
                BillItem(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    gst_rate=item["gst_rate"],
                    taxable_amount=item["taxable_amount"],
                    cgst=item["cgst"],
                    sgst=item["sgst"],
                    line_total=item["line_total"]
                )
            )

        bill.subtotal = calculated["subtotal"]
        bill.cgst = calculated["cgst"]
        bill.sgst = calculated["sgst"]
        bill.total = calculated["total"]

        self.db.commit()
        self.db.refresh(bill)

        return bill

    # ---------------------------------------------------------
    # FINALIZE BILL
    # ---------------------------------------------------------

    def finalize_bill(
        self,
        bill_number: str,
        payment_mode: str,
        payment_reference: str | None = None
    ):

        bill = self.db.scalar(
            select(Bill).where(
                Bill.bill_number ==
                bill_number
            )
        )

        if not bill:
            raise ValueError(
                "BILL_NOT_FOUND"
            )

        # Idempotency:
        # retrying finalization must not create another sale.
        if bill.status == "FINALIZED":
            return bill

        if bill.status != "DRAFT":
            raise ValueError(
                f"BILL_NOT_DRAFT:{bill.status}"
            )

        payment_mode = payment_mode.upper()

        allowed_payment_modes = {
            "CASH",
            "UPI",
            "CARD",
            "CREDIT"
        }

        if payment_mode not in allowed_payment_modes:
            raise ValueError(
                "INVALID_PAYMENT_MODE"
            )

        # -----------------------------------------------------
        # AUTHORITATIVE STOCK CHECK
        # -----------------------------------------------------

        for item in bill.items:

            product = self.db.get(
                Product,
                item.product_id
            )

            if not product:

                self.db.rollback()

                raise ValueError(
                    f"PRODUCT_NOT_FOUND:{item.product_id}"
                )

            if product.sell_price < product.cost_price:

                self.db.rollback()

                raise ValueError(
                    f"SELL_PRICE_BELOW_COST:{product.name}"
                )

            if item.quantity > product.quantity:

                self.db.rollback()

                raise ValueError(
                    f"INSUFFICIENT_STOCK:{product.name}"
                )

        # -----------------------------------------------------
        # DEDUCT STOCK
        # -----------------------------------------------------

        for item in bill.items:

            product = self.db.get(
                Product,
                item.product_id
            )

            product.quantity -= item.quantity

        # -----------------------------------------------------
        # FINALIZE
        # -----------------------------------------------------

        bill.status = "FINALIZED"

        bill.payment_mode = payment_mode

        bill.payment_reference = (
            payment_reference
        )

        bill.finalized_at = (
            datetime.utcnow()
        )

        self.db.commit()
        self.db.refresh(bill)

        return bill