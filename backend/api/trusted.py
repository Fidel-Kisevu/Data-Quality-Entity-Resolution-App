from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from core.database import get_db
from services.trusted import (
    list_trusted_customers,
    get_trusted_customer,
    list_trusted_transactions,
    export_trusted_customers_csv,
)

router = APIRouter()


@router.get("/customers")
def trusted_customers(
    limit: int = Query(500, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_trusted_customers(db, limit=limit, offset=offset)


@router.get("/customers/{customer_id}")
def trusted_customer(customer_id: str, db: Session = Depends(get_db)):
    result = get_trusted_customer(db, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Trusted customer not found")
    return result


@router.get("/transactions")
def trusted_transactions(
    limit: int = Query(500, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_trusted_transactions(db, limit=limit, offset=offset)


@router.get("/export", response_class=PlainTextResponse)
def export_trusted(db: Session = Depends(get_db)):
    csv_text = export_trusted_customers_csv(db)
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="trusted_customers.csv"'},
    )