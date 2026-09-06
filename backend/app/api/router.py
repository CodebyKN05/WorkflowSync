from fastapi import APIRouter
from app.api import auth, invoices, transactions, reconciliation, firms, clients

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["reconciliation"])
api_router.include_router(firms.router, prefix="/firms", tags=["firms"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
# Future domain routers will be included here
