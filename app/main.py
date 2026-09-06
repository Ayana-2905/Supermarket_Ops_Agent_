from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.database import Base, engine, get_db
from app.infrastructure.database import models
from app.domain.inventory.service import InventoryService
Base.metadata.create_all(bind=engine)

from app.domain.inventory.schemas import (
    AddProductRequest,
    ReceiveStockRequest
)

app = FastAPI(
    title=" KiranaPilot",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "kirana-pilot"
    }

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
    service = InventoryService(db)

    product = service.get_product(product_id)

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


@app.get("/debug/stock/{product_id}")
def get_stock(
    product_id: int,
    db: Session = Depends(get_db)
):
    service = InventoryService(db)

    return service.get_stock(product_id)


@app.get("/debug/low-stock")
def low_stock(
    db: Session = Depends(get_db)
):
    service = InventoryService(db)

    return service.get_low_stock()


@app.post("/debug/products")
def add_product(
    request: AddProductRequest,
    db: Session = Depends(get_db)
):
    service = InventoryService(db)

    product = service.add_product(request)

    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "quantity": product.quantity
    }


@app.post("/debug/stock/receive")
def receive_stock(
    request: ReceiveStockRequest,
    db: Session = Depends(get_db)
):
    service = InventoryService(db)

    return service.receive_stock(request)