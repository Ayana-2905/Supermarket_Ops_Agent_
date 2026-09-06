from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    Customer,
    KhataTransaction
)

from app.domain.khata.schemas import (
    AddCreditRequest,
    SettleCreditRequest
)


class KhataService:

    def __init__(self, db: Session):
        self.db = db

    def _get_customer(self, name: str):

        name = name.strip()

        if not name:
            raise ValueError("CUSTOMER_NAME_REQUIRED")

        statement = (
            select(Customer)
            .where(Customer.name.ilike(name))
        )

        customer = self.db.scalar(statement)

        if not customer:
            raise ValueError("CUSTOMER_NOT_FOUND")

        return customer

    def _get_or_create_customer(self, name: str):

        name = name.strip()

        if not name:
            raise ValueError("CUSTOMER_NAME_REQUIRED")

        statement = (
            select(Customer)
            .where(Customer.name.ilike(name))
        )

        customer = self.db.scalar(statement)

        if customer:
            return customer

        customer = Customer(name=name)

        self.db.add(customer)
        self.db.flush()

        return customer

    def add_credit(self, request: AddCreditRequest):

        if request.amount <= 0:
            raise ValueError("CREDIT_AMOUNT_MUST_BE_POSITIVE")

        customer = self._get_or_create_customer(
            request.customer_name
        )

        transaction = KhataTransaction(
            customer_id=customer.id,
            transaction_type="CREDIT",
            amount=request.amount,
            reference=request.reference
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return self.get_balance(customer.name)

    def settle_credit(self, request: SettleCreditRequest):

        if request.amount <= 0:
            raise ValueError("SETTLEMENT_AMOUNT_MUST_BE_POSITIVE")

        customer = self._get_customer(
            request.customer_name
        )

        # Lock customer while checking and recording payment
        customer = self.db.scalar(
            select(Customer)
            .where(Customer.id == customer.id)
            .with_for_update()
        )

        balance = self.get_balance(customer.name)

        if request.amount > balance["balance"]:
            self.db.rollback()
            raise ValueError(
                "SETTLEMENT_EXCEEDS_BALANCE"
            )

        transaction = KhataTransaction(
            customer_id=customer.id,
            transaction_type="PAYMENT",
            amount=request.amount,
            reference=request.reference
        )

        self.db.add(transaction)
        self.db.commit()

        return self.get_balance(customer.name)

    def get_balance(self, customer_name: str):

        customer = self._get_customer(
            customer_name
        )

        credit_statement = (
            select(
                func.coalesce(
                    func.sum(
                        KhataTransaction.amount
                    ),
                    0
                )
            )
            .where(
                KhataTransaction.customer_id == customer.id,
                KhataTransaction.transaction_type == "CREDIT"
            )
        )

        payment_statement = (
            select(
                func.coalesce(
                    func.sum(
                        KhataTransaction.amount
                    ),
                    0
                )
            )
            .where(
                KhataTransaction.customer_id == customer.id,
                KhataTransaction.transaction_type == "PAYMENT"
            )
        )

        total_credit = self.db.scalar(
            credit_statement
        ) or 0

        total_payment = self.db.scalar(
            payment_statement
        ) or 0

        balance = total_credit - total_payment

        return {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "total_credit": round(total_credit, 2),
            "total_paid": round(total_payment, 2),
            "balance": round(balance, 2)
        }

    def get_transactions(self, customer_name: str):

        customer = self._get_customer(
            customer_name
        )

        statement = (
            select(KhataTransaction)
            .where(
                KhataTransaction.customer_id == customer.id
            )
            .order_by(
                KhataTransaction.created_at
            )
        )

        transactions = self.db.scalars(
            statement
        ).all()

        return [
            {
                "id": transaction.id,
                "type": transaction.transaction_type,
                "amount": transaction.amount,
                "reference": transaction.reference,
                "created_at": transaction.created_at.isoformat()
            }
            for transaction in transactions
        ]