from pydantic import BaseModel, Field


class BillItemRequest(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)


class CreateBillRequest(BaseModel):
    items: list[BillItemRequest]

    customer_id: int | None = None

    idempotency_key: str | None = None