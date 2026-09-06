from pydantic import BaseModel, Field


class AddProductRequest(BaseModel):
    name: str = Field(min_length=2)
    sku: str = Field(min_length=2)
    category: str | None = None

    unit: str = Field(min_length=1)
    is_loose: bool = False

    cost_price: float = Field(ge=0)
    sell_price: float = Field(ge=0)
    mrp: float = Field(ge=0)

    quantity: float = Field(default=0, ge=0)
    reorder_level: float = Field(default=5, ge=0)

    gst_rate: float = Field(default=0, ge=0, le=100)
    hsn_code: str | None = None


class ReceiveStockRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: float = Field(gt=0)

    cost_price: float | None = Field(
        default=None,
        ge=0
    )

    mrp: float | None = Field(
        default=None,
        ge=0
    )