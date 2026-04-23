import json
from typing import Literal, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import check_idempotency, get_idempotency_key, store_idempotency
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseRead

router = APIRouter()


@router.get("/healthz")
def healthz():
    return {"status": "ok"}


@router.post("/expenses", status_code=201)
def create_expense(
    body: ExpenseCreate,
    idempotency_key: str = Depends(get_idempotency_key),
    db: Session = Depends(get_db),
):
    cached = check_idempotency(idempotency_key, db)
    if cached:
        return JSONResponse(status_code=cached.status_code, content=json.loads(cached.response_body))

    amount_minor = int(body.amount * 100)
    expense = Expense(
        amount_minor=amount_minor,
        category=body.category,
        description=body.description,
        date=body.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    read = ExpenseRead.from_orm_expense(expense)
    response_body = read.model_dump_json()
    store_idempotency(idempotency_key, response_body, 201, db)

    return JSONResponse(status_code=201, content=json.loads(response_body))


@router.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(
    category: Optional[str] = None,
    sort: Literal["date_asc", "date_desc"] = "date_desc",
    db: Session = Depends(get_db),
):
    query = db.query(Expense)
    if category:
        query = query.filter(Expense.category == category)
    if sort == "date_desc":
        query = query.order_by(Expense.date.desc(), Expense.id.desc())
    else:
        query = query.order_by(Expense.date.asc(), Expense.id.asc())
    expenses = query.all()
    return [ExpenseRead.from_orm_expense(e) for e in expenses]
