from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)

    category: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(30))
    is_loose: Mapped[bool] = mapped_column(Boolean, default=False)

    cost_price: Mapped[float] = mapped_column(Float)
    sell_price: Mapped[float] = mapped_column(Float)
    mrp: Mapped[float] = mapped_column(Float)

    quantity: Mapped[float] = mapped_column(Float, default=0)
    reorder_level: Mapped[float] = mapped_column(Float, default=5)

    gst_rate: Mapped[float] = mapped_column(Float, default=0)
    hsn_code: Mapped[str | None] = mapped_column(String(30))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(150), index=True)

    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)

    bill_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="DRAFT"
    )

    subtotal: Mapped[float] = mapped_column(Float, default=0)
    cgst: Mapped[float] = mapped_column(Float, default=0)
    sgst: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)

    payment_mode: Mapped[str | None] = mapped_column(
        String(30)
    )

    payment_reference: Mapped[str | None] = mapped_column(
        String(100)
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(100),
        unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    items = relationship(
        "BillItem",
        back_populates="bill",
        cascade="all, delete-orphan"
    )


class BillItem(Base):
    __tablename__ = "bill_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    bill_id: Mapped[int] = mapped_column(
        ForeignKey("bills.id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    quantity: Mapped[float] = mapped_column(Float)

    unit_price: Mapped[float] = mapped_column(Float)

    gst_rate: Mapped[float] = mapped_column(Float)

    taxable_amount: Mapped[float] = mapped_column(Float)

    cgst: Mapped[float] = mapped_column(Float)

    sgst: Mapped[float] = mapped_column(Float)

    line_total: Mapped[float] = mapped_column(Float)

    bill = relationship(
        "Bill",
        back_populates="items"
    )
    product = relationship(
    "Product"
    )


class KhataTransaction(Base):
    __tablename__ = "khata_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id")
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20)
    )

    amount: Mapped[float] = mapped_column(Float)

    reference: Mapped[str | None] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    value: Mapped[str] = mapped_column(Text)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_update_id: Mapped[str | None] = mapped_column(
        String(100)
    )

    conversation_id: Mapped[str | None] = mapped_column(
        String(100)
    )

    event_type: Mapped[str] = mapped_column(
        String(50)
    )

    tool_name: Mapped[str | None] = mapped_column(
        String(100)
    )

    arguments: Mapped[str | None] = mapped_column(Text)

    result: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(30))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class ProcessedUpdate(Base):
    __tablename__ = "processed_updates"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_update_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )