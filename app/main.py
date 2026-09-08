from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.database.database import (
    Base,
    engine,
    get_db
)

from app.infrastructure.database import models

from app.domain.inventory.service import InventoryService
from app.domain.inventory.schemas import (
    AddProductRequest,
    ReceiveStockRequest
)

from app.domain.billing.schemas import CreateBillRequest
from app.domain.billing.service import BillingService
from app.domain.billing.schemas import (
    CreateBillRequest,
    BillItemRequest
)

from app.domain.khata.service import KhataService
from app.domain.khata.schemas import (
    AddCreditRequest,
    SettleCreditRequest
)
from app.agent.tools import generate_sales_analysis

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="KiranaPilot",
    version="0.1.0"
)


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": "kirana-pilot"
    }


# =========================================================
# INVENTORY
# =========================================================

@app.get("/debug/products")
def search_products(
    query: str,
    db: Session = Depends(get_db)
):

    service = InventoryService(db)

    products = service.search_products(query)

    return [
        {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "quantity": product.quantity,
            "unit": product.unit,
            "sell_price": product.sell_price,
            "mrp": product.mrp,
            "gst_rate": product.gst_rate
        }
        for product in products
    ]


@app.get("/debug/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    try:

        service = InventoryService(db)

        product = service.get_product(
            product_id
        )

        return {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "quantity": product.quantity,
            "unit": product.unit,
            "cost_price": product.cost_price,
            "sell_price": product.sell_price,
            "mrp": product.mrp,
            "gst_rate": product.gst_rate
        }

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@app.get("/debug/stock/{product_id}")
def get_stock(
    product_id: int,
    db: Session = Depends(get_db)
):

    try:

        service = InventoryService(db)

        return service.get_stock(
            product_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@app.get("/debug/low-stock")
def low_stock(
    db: Session = Depends(get_db)
):

    service = InventoryService(db)

    return service.get_low_stock()


@app.get("/debug/inventory")
def list_inventory(
    db: Session = Depends(get_db)
):

    service = InventoryService(db)

    return service.list_products()


@app.get("/debug/inventory/count")
def count_inventory(
    db: Session = Depends(get_db)
):

    service = InventoryService(db)

    return service.count_products()


@app.get("/debug/inventory/quantity")
def total_inventory_quantity(
    db: Session = Depends(get_db)
):

    service = InventoryService(db)

    return service.get_total_quantity()


@app.post("/debug/products")
def add_product(
    request: AddProductRequest,
    db: Session = Depends(get_db)
):

    try:

        service = InventoryService(db)

        product = service.add_product(
            request
        )

        return {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "quantity": product.quantity
        }

    except ValueError as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.post("/debug/stock/receive")
def receive_stock(
    request: ReceiveStockRequest,
    db: Session = Depends(get_db)
):

    try:

        service = InventoryService(db)

        return service.receive_stock(
            request
        )

    except ValueError as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =========================================================
# BILLING
# =========================================================

@app.post("/debug/bills")
def create_bill(
    request: CreateBillRequest,
    db: Session = Depends(get_db)
):

    try:

        service = BillingService(db)

        bill = service.create_draft_bill(
            request
        )

        return {
            "bill_number": bill.bill_number,
            "status": bill.status,
            "subtotal": bill.subtotal,
            "cgst": bill.cgst,
            "sgst": bill.sgst,
            "total": bill.total
        }

    except ValueError as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.get("/debug/bills/{bill_number}")
def get_bill(
    bill_number: str,
    db: Session = Depends(get_db)
):

    try:

        service = BillingService(db)

        bill = service.get_draft_bill(
            bill_number
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
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "gst_rate": item.gst_rate,
                    "line_total": item.line_total
                }
                for item in bill.items
            ]
        }

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# =========================================================
# KHATA
# =========================================================

@app.post("/debug/khata/credit")
def add_khata_credit(
    request: AddCreditRequest,
    db: Session = Depends(get_db)
):
    service = KhataService(db)

    return service.add_credit(request)


@app.post("/debug/khata/settle")
def settle_khata(
    request: SettleCreditRequest,
    db: Session = Depends(get_db)
):
    service = KhataService(db)

    return service.settle_credit(request)


@app.get("/debug/khata/{customer_name}")
def get_khata_balance(
    customer_name: str,
    db: Session = Depends(get_db)
):
    service = KhataService(db)

    return service.get_balance(customer_name)


@app.get("/debug/khata/{customer_name}/transactions")
def get_khata_transactions(
    customer_name: str,
    db: Session = Depends(get_db)
):
    service = KhataService(db)

    return {
        "transactions": service.get_transactions(customer_name)
    }
# =========================================================
# OWNER PREFERENCES
# =========================================================

from app.domain.preferences.service import PreferenceService



@app.post("/debug/preferences")
def set_preference(
    key: str,
    value: str,
    db: Session = Depends(get_db)
):
    service = PreferenceService(db)

    return service.set_preference(
        key,
        value
    )


@app.get("/debug/preferences")
def get_preferences(
    db: Session = Depends(get_db)
):
    service = PreferenceService(db)

    return service.get_all_preferences()


@app.post("/debug/bills")
def create_bill(
    request: CreateBillRequest,
    db: Session = Depends(get_db)
):
    service = BillingService(db)

    bill = service.create_draft_bill(request)

    return {
        "bill_number": bill.bill_number,
        "status": bill.status,
        "subtotal": bill.subtotal,
        "cgst": bill.cgst,
        "sgst": bill.sgst,
        "total": bill.total
    }


@app.get("/debug/bills/{bill_number}")
def get_bill(
    bill_number: str,
    db: Session = Depends(get_db)
):
    service = BillingService(db)

    bill = service.get_draft_bill(bill_number)

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
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "gst_rate": item.gst_rate,
                "line_total": item.line_total
            }
            for item in bill.items
        ]
    }
@app.put("/debug/bills/{bill_number}")
def edit_bill(
    bill_number: str,
    request: CreateBillRequest,
    db: Session = Depends(get_db)
):
    service = BillingService(db)

    bill = service.edit_draft_bill(
        bill_number,
        request.items
    )

    return {
        "bill_number": bill.bill_number,
        "status": bill.status,
        "subtotal": bill.subtotal,
        "cgst": bill.cgst,
        "sgst": bill.sgst,
        "total": bill.total
    }
@app.post("/debug/bills/{bill_number}/finalize")
def finalize_bill(
    bill_number: str,
    db: Session = Depends(get_db)
):
    service = BillingService(db)

    bill = service.finalize_bill(
        bill_number=bill_number,
        payment_mode="CASH"
    )

    return {
        "bill_number": bill.bill_number,
        "status": bill.status,
        "payment_mode": bill.payment_mode,
        "total": bill.total,
        "finalized_at": bill.finalized_at
    }

@app.get("/debug/sales-analysis")
def sales_analysis(days: int = 7):
    return generate_sales_analysis(days)