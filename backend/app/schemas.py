from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    model_config = {"extra": "forbid"}

    amount: Decimal = Field(..., decimal_places=2, gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)
    date: str = Field(...)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            parsed = date.fromisoformat(v)
        except ValueError:
            raise ValueError("date must be a valid ISO 8601 date (YYYY-MM-DD)")
        if parsed > date.today() + timedelta(days=1):
            raise ValueError("date must not be more than 1 day in the future")
        return v


class ExpenseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    amount: Decimal
    category: str
    description: str
    date: str
    created_at: datetime

    @classmethod
    def from_orm_expense(cls, expense) -> "ExpenseRead":
        return cls(
            id=expense.id,
            amount=(Decimal(expense.amount_minor) / Decimal("100")).quantize(Decimal("0.01")),
            category=expense.category,
            description=expense.description,
            date=expense.date,
            created_at=expense.created_at,
        )
