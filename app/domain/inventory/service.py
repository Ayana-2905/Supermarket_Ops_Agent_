from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Product
from app.domain.inventory.schemas import (
    AddProductRequest,
    ReceiveStockRequest
)


class InventoryService:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    def search_products(self, query: str):

        query = query.strip()

        if not query:
            return []

        statement = (
            select(Product)
            .where(
                Product.name.ilike(f"%{query}%")
            )
            .order_by(Product.name)
        )

        return self.db.scalars(statement).all()

    # ---------------------------------------------------------
    # GET PRODUCT
    # ---------------------------------------------------------

    def get_product(self, product_id: int):

        product = self.db.get(
            Product,
            product_id
        )

        if not product:
            raise ValueError(
                "PRODUCT_NOT_FOUND"
            )

        return product

    # ---------------------------------------------------------
    # GET STOCK
    # ---------------------------------------------------------

    def get_stock(self, product_id: int):

        product = self.get_product(
            product_id
        )

        return {
            "product_id": product.id,
            "name": product.name,
            "sku": product.sku,
            "quantity": product.quantity,
            "unit": product.unit,
            "reorder_level": product.reorder_level,
            "low_stock": (
                product.quantity
                <= product.reorder_level
            )
        }

    # ---------------------------------------------------------
    # ADD PRODUCT
    # ---------------------------------------------------------

    def add_product(
        self,
        request: AddProductRequest
    ):

        existing = self.db.scalar(
            select(Product).where(
                Product.sku == request.sku
            )
        )

        if existing:
            raise ValueError(
                "SKU_ALREADY_EXISTS"
            )

        if request.quantity < 0:
            raise ValueError(
                "QUANTITY_CANNOT_BE_NEGATIVE"
            )

        if request.sell_price > request.mrp:
            raise ValueError(
                "SELLING_PRICE_CANNOT_EXCEED_MRP"
            )

        if request.sell_price < request.cost_price:
            raise ValueError(
                "SELLING_PRICE_BELOW_COST"
            )

        product = Product(
            name=request.name,
            sku=request.sku,
            category=request.category,
            unit=request.unit,
            is_loose=request.is_loose,
            cost_price=request.cost_price,
            sell_price=request.sell_price,
            mrp=request.mrp,
            quantity=request.quantity,
            reorder_level=request.reorder_level,
            gst_rate=request.gst_rate,
            hsn_code=request.hsn_code
        )

        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        return product

    # ---------------------------------------------------------
    # RECEIVE STOCK
    # ---------------------------------------------------------

    def receive_stock(
        self,
        request: ReceiveStockRequest
    ):

        if request.quantity <= 0:
            raise ValueError(
                "RECEIVED_QUANTITY_MUST_BE_POSITIVE"
            )

        product = self.get_product(
            request.product_id
        )

        old_quantity = product.quantity

        product.quantity += request.quantity

        if request.cost_price is not None:

            if request.cost_price <= 0:
                raise ValueError(
                    "COST_PRICE_MUST_BE_POSITIVE"
                )

            product.cost_price = (
                request.cost_price
            )

        if request.mrp is not None:

            if request.mrp <= 0:
                raise ValueError(
                    "MRP_MUST_BE_POSITIVE"
                )

            product.mrp = request.mrp

        if product.sell_price > product.mrp:

            self.db.rollback()

            raise ValueError(
                "SELLING_PRICE_CANNOT_EXCEED_MRP"
            )

        self.db.commit()
        self.db.refresh(product)

        return {
            "product_id": product.id,
            "name": product.name,
            "previous_quantity": old_quantity,
            "received_quantity": request.quantity,
            "new_quantity": product.quantity
        }

    # ---------------------------------------------------------
    # LOW STOCK
    # ---------------------------------------------------------

    def get_low_stock(self):

        statement = (
            select(Product)
            .where(
                Product.quantity
                <= Product.reorder_level
            )
            .order_by(Product.quantity)
        )

        products = self.db.scalars(
            statement
        ).all()

        return [
            {
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "quantity": product.quantity,
                "reorder_level": product.reorder_level,
                "unit": product.unit
            }
            for product in products
        ]

    # ---------------------------------------------------------
    # COUNT PRODUCTS
    # ---------------------------------------------------------

    def count_products(self):

        statement = select(Product)

        products = self.db.scalars(
            statement
        ).all()

        return {
            "product_count": len(products)
        }

    # ---------------------------------------------------------
    # LIST PRODUCTS
    # ---------------------------------------------------------

    def list_products(self):

        statement = (
            select(Product)
            .order_by(Product.name)
        )

        products = self.db.scalars(
            statement
        ).all()

        return [
            {
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
            for product in products
        ]

    # ---------------------------------------------------------
    # TOTAL INVENTORY QUANTITY
    # ---------------------------------------------------------

    def get_total_quantity(self):

        statement = select(Product)

        products = self.db.scalars(
            statement
        ).all()

        total_quantity = sum(
            product.quantity
            for product in products
        )

        return {
            "total_quantity": total_quantity,
            "product_count": len(products)
        }