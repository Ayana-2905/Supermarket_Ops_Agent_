from pydantic import BaseModel, Field


class AddCreditRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    amount: float = Field(gt=0)
    reference: str | None = None


class SettleCreditRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    amount: float = Field(gt=0)
    reference: str | None = None