from fastapi import APIRouter
from app.api import auth, invoices, transactions, reconciliation

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["reconciliation"])
# Future domain routers will be included here
