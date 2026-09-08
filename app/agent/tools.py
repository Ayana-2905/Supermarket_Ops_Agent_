from agents import function_tool
from pydantic import BaseModel
from dataclasses import dataclass
from agents import RunContextWrapper

from app.domain.preferences.service import PreferenceService
from datetime import datetime, timedelta
from sqlalchemy import func

from app.infrastructure.database.database import SessionLocal
from app.domain.inventory.service import InventoryService

from app.domain.billing.service import BillingService
from app.documents.analysis_deck import generate_sales_analysis_deck

from app.documents.invoice import generate_invoice_pdf
from app.domain.inventory.schemas import (
    AddProductRequest,
    ReceiveStockRequest
)
from app.domain.billing.schemas import (
    CreateBillRequest,
    BillItemRequest
)

from app.domain.billing.confirmation_instance import (
    confirmation_manager
)
from app.domain.khata.service import KhataService
from app.domain.khata.schemas import(
    AddCreditRequest,
    SettleCreditRequest
)

from sqlalchemy import select

from app.infrastructure.database.models import (
    Product,
    Bill
)

from app.domain.billing.service import BillingService


@dataclass
class TelegramContext:
    chat_id: str

def product_to_dict(product):
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "category": product.category,
        "unit": product.unit,
        "quantity": product.quantity,
        "sell_price": product.sell_price,
        "mrp": product.mrp,
        "gst_rate": product.gst_rate
    }

@function_tool
def search_products(query: str) -> list[dict]:
    """
    Search the store's product catalog.

    Use this when the owner mentions a product but
    the exact product record is not known.
    """

    db = SessionLocal()

    try:
        service = InventoryService(db)

        products = service.search_products(query)

        return [
            product_to_dict(product)
            for product in products
        ]

    finally:
        db.close()


@function_tool
def get_product(product_id: int) -> dict:
    """
    Get authoritative information about a specific
    product from the store database.
    """

    db = SessionLocal()

    try:
        service = InventoryService(db)

        product = service.get_product(product_id)

        return product_to_dict(product)

    finally:
        db.close()


@function_tool
def get_stock(product_id: int) -> dict:
    """
    Get the current stock level for a product.
    """

    db = SessionLocal()

    try:
        service = InventoryService(db)

        return service.get_stock(product_id)

    finally:
        db.close()


@function_tool
def get_low_stock(dummy: str = "") -> list[dict]:
    """
    Find all products whose stock is at or below
    their configured reorder level.
    """

    db = SessionLocal()

    try:
        service = InventoryService(db)

        return service.get_low_stock()

    finally:
        db.close()


@function_tool
def add_product(
    name: str,
    sku: str,
    unit: str,
    cost_price: float,
    sell_price: float,
    mrp: float,
    category: str | None = None,
    is_loose: bool = False,
    quantity: float = 0,
    reorder_level: float = 5,
    gst_rate: float = 0,
    hsn_code: str | None = None
) -> dict:
    """
    Add a new product to the store catalog.

    The tool validates SKU uniqueness and price rules.
    """

    db = SessionLocal()

    try:

        request = AddProductRequest(
            name=name,
            sku=sku,
            category=category,
            unit=unit,
            is_loose=is_loose,
            cost_price=cost_price,
            sell_price=sell_price,
            mrp=mrp,
            quantity=quantity,
            reorder_level=reorder_level,
            gst_rate=gst_rate,
            hsn_code=hsn_code
        )

        service = InventoryService(db)

        product = service.add_product(request)

        return product_to_dict(product)

    finally:
        db.close()


@function_tool
def receive_stock(
    product_id: int,
    quantity: float,
    cost_price: float | None = None,
    mrp: float | None = None
) -> dict:
    """
    Record incoming stock for an existing product.

    Stock is increased only after the service validates
    the request.
    """

    db = SessionLocal()

    try:

        request = ReceiveStockRequest(
            product_id=product_id,
            quantity=quantity,
            cost_price=cost_price,
            mrp=mrp
        )

        service = InventoryService(db)

        return service.receive_stock(request)

    finally:
        db.close()

@function_tool
def count_products(dummy: str = "") -> dict:
    """
    Count the number of products currently registered
    in the store inventory.
    """
    db = SessionLocal()

    try:
        service = InventoryService(db)
        return service.count_products()
    finally:
        db.close()

@function_tool
def list_inventory(dummy: str = "") -> list[dict]:
    """
    List all products currently registered in the store.

    Use this when the owner asks for:
    - all products
    - available products
    - inventory
    - product catalog
    - everything in stock
    - what products are available
    """

    db = SessionLocal()

    try:
        service = InventoryService(db)

        return service.list_products()

    finally:
        db.close()


@function_tool
def get_total_inventory_quantity(dummy: str = "") -> dict:
    """
    Calculate the total quantity of all products
    currently present in the inventory.

    Use this when the owner asks:
    - total quantity
    - total stock
    - how many items are in the store
    - total inventory quantity
    """

    db = SessionLocal()

    try:
        service = InventoryService(db)

        return service.get_total_quantity()

    finally:
        db.close()

class BillItemInput(BaseModel):
    product_id: int
    quantity: float
@function_tool
def create_draft_bill(
    ctx: RunContextWrapper[TelegramContext],
    items: list[BillItemInput],
    customer_id: int | None = None
) -> dict:

    db = SessionLocal()

    try:
        bill_items = [
            BillItemRequest(
                product_id=item.product_id,
                quantity=item.quantity
            )
            for item in items
        ]

        request = CreateBillRequest(
            items=bill_items,
            customer_id=customer_id
        )

        service = BillingService(db)

        bill = service.create_draft_bill(request)

        chat_id = ctx.context.chat_id

        print(
            f"[BILL] Created draft {bill.bill_number}"
        )

        print(
            f"[BILL] Telegram chat_id = {chat_id}"
        )

        confirmation_manager.set_pending(
            chat_id,
            bill.bill_number
        )

        print(
            f"[BILL] Pending confirmation stored for chat_id={chat_id}"
        )

        return {
            "bill_number": bill.bill_number,
            "status": bill.status,
            "subtotal": bill.subtotal,
            "cgst": bill.cgst,
            "sgst": bill.sgst,
            "total": bill.total
        }

    except Exception as e:

        db.rollback()

        print(f"[BILL ERROR] {e}")

        return {
            "error": str(e)
        }

    finally:
        db.close()

@function_tool
def edit_draft_bill(
    bill_number: str,
    items: list[BillItemInput]
) -> dict:
    """
    Edit the current DRAFT BILL.

    Use this to:
    - change an item's quantity
    - remove an item
    - add an item
    - replace the bill contents

    The items list represents the COMPLETE desired contents
    of the draft bill.

    Do NOT use this tool to change inventory stock.
    """

    db = SessionLocal()

    try:

        service = BillingService(db)

        bill_items = [
            BillItemRequest(
                product_id=item.product_id,
                quantity=item.quantity
            )
            for item in items
        ]

        bill = service.edit_draft_bill(
            bill_number,
            bill_items
        )

        return {
            "bill_number": bill.bill_number,
            "status": bill.status,
            "subtotal": bill.subtotal,
            "cgst": bill.cgst,
            "sgst": bill.sgst,
            "total": bill.total
        }

    except Exception as e:

        db.rollback()

        return {
            "error": str(e)
        }

    finally:
        db.close()

@function_tool
def get_pending_bill(chat_id: str) -> dict:
    """
    Get the pending draft bill associated with the current Telegram chat.
    """

    pending = confirmation_manager.get_pending(chat_id)

    if not pending:
        return {
            "error": "NO_PENDING_BILL"
        }

    db = SessionLocal()

    try:
        service = BillingService(db)

        bill = service.get_draft_bill(
            pending.bill_number
        )

        return {
            "bill_number": bill.bill_number,
            "status": bill.status,
            "subtotal": bill.subtotal,
            "cgst": bill.cgst,
            "sgst": bill.sgst,
            "total": bill.total,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": (
                        item.product.name
                        if item.product
                        else f"Product #{item.product_id}"
                    ),
                    "quantity": item.quantity,
                    "unit_price": item.unit_price
                }
                for item in bill.items
            ]
        }

    finally:
        db.close()

def is_confirmation(text: str) -> bool:
    confirmations = {
        "yes",
        "yes confirm",
        "confirm bill"
        "confirm",
        "confirmed",
        "proceed",
        "go ahead",
        "okay",
        "ok",
        "yes finalize"
        }

    normalized = text.strip().lower()

    return normalized in confirmations

def is_cancellation(text: str) -> bool:
    cancellations = {
        "no",
        "cancel",
        "cancel it",
        "cancel bill",
        "stop",
        "don't",
        "do not"
    }

    normalized = text.strip().lower()

    return normalized in cancellations  

def _confirm_pending_bill(
    chat_id: str,
    payment_mode: str,
    payment_reference: str
) -> dict:

    pending = confirmation_manager.get_pending(chat_id)

    if not pending:
        return {
            "error": "NO_PENDING_BILL"
        }

    db = SessionLocal()

    try:
        service = BillingService(db)

        bill = service.finalize_bill(
            pending.bill_number,
            payment_mode,
            payment_reference if payment_reference else None
        )

        confirmation_manager.clear(chat_id)

        return {
            "bill_number": bill.bill_number,
            "status": bill.status,
            "payment_mode": bill.payment_mode,
            "payment_reference": bill.payment_reference,
            "total": bill.total
        }

    except Exception as e:

        db.rollback()

        return {
            "error": str(e)
        }

    finally:
        db.close()

@function_tool
def confirm_pending_bill(
    chat_id: str,
    payment_mode: str = "CASH",
    payment_reference: str = ""
) -> dict:

    return _confirm_pending_bill(
        chat_id=chat_id,
        payment_mode=payment_mode,
        payment_reference=payment_reference
    )

@function_tool
def add_khata_credit(
    customer_name: str,
    amount: float,
    reference: str | None = None
) -> dict:

    db = SessionLocal()

    try:
        service = KhataService(db)

        request = AddCreditRequest(
            customer_name=customer_name,
            amount=amount,
            reference=reference
        )

        return service.add_credit(request)

    finally:
        db.close()
@function_tool
def settle_khata(
    customer_name: str,
    amount: float,
    reference: str | None = None
) -> dict:

    db = SessionLocal()

    try:
        service = KhataService(db)

        request = SettleCreditRequest(
            customer_name=customer_name,
            amount=amount,
            reference=reference
        )

        return service.settle_credit(request)

    finally:
        db.close()
@function_tool
def get_khata_balance(
    customer_name: str
) -> dict:

    db = SessionLocal()

    try:
        service = KhataService(db)

        return service.get_balance(
            customer_name
        )

    finally:
        db.close()

@function_tool
def get_khata_transactions(
    customer_name: str
) -> dict:

    db = SessionLocal()

    try:
        service = KhataService(db)

        return {
            "transactions": service.get_transactions(
                customer_name
            )
        }

    finally:
        db.close()

def _generate_invoice(bill_number: str) -> dict:
    """
    Internal Python function for generating a GST invoice PDF.
    """

    db = SessionLocal()

    try:
        bill = db.scalar(
            select(Bill).where(
                Bill.bill_number == bill_number
            )
        )

        if not bill:
            return {
                "error": "BILL_NOT_FOUND"
            }

        if bill.status != "FINALIZED":
            return {
                "error": "BILL_NOT_FINALIZED"
            }

        file_path = generate_invoice_pdf(bill)

        return {
            "bill_number": bill.bill_number,
            "status": bill.status,
            "invoice_path": file_path
        }

    except Exception as e:
        return {
            "error": str(e)
        }

    finally:
        db.close()


@function_tool
def generate_invoice(bill_number: str) -> dict:
    """
    Generate a GST invoice PDF for a finalized bill.
    """
    return _generate_invoice(bill_number)

@function_tool
def get_daily_sales_summary(dummy: str = "") -> dict:
    """
    Return today's finalized sales summary.

    Includes:
    - number of finalized bills
    - subtotal
    - CGST
    - SGST
    - total sales
    """

    db = SessionLocal()

    try:
        start = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        end = start + timedelta(days=1)

        bills = db.scalars(
            select(Bill).where(
                Bill.status == "FINALIZED",
                Bill.finalized_at >= start,
                Bill.finalized_at < end
            )
        ).all()

        return {
            "date": start.strftime("%Y-%m-%d"),
            "bill_count": len(bills),
            "subtotal": round(
                sum(b.subtotal for b in bills), 2
            ),
            "cgst": round(
                sum(b.cgst for b in bills), 2
            ),
            "sgst": round(
                sum(b.sgst for b in bills), 2
            ),
            "total_sales": round(
                sum(b.total for b in bills), 2
            )
        }

    finally:
        db.close()


@function_tool
def set_owner_preference(
    key: str,
    value: str
) -> dict:
    """
    Save a store owner's preference permanently.

    Use this when the owner explicitly asks you to remember
    a preference for future conversations.
    """

    db = SessionLocal()

    try:
        service = PreferenceService(db)

        return service.set_preference(
            key,
            value
        )

    finally:
        db.close()


@function_tool
def get_owner_preferences(dummy: str = "") -> dict:
    """
    Retrieve all permanently saved owner preferences.
    """

    db = SessionLocal()

    try:
        service = PreferenceService(db)

        return service.get_all_preferences()

    finally:
        db.close()

@function_tool
def generate_sales_analysis(days: int = 7) -> dict:
    """
    Generate a PowerPoint sales analysis deck.

    Includes:
    - total sales
    - total bills
    - average bill value
    - daily sales chart

    Default period is the last 7 days.
    """
    try:
        file_path = generate_sales_analysis_deck(days)

        return {
            "status": "success",
            "days": days,
            "file_path": file_path
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }