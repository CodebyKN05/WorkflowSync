from fastapi import FastAPI
from app.api.router import api_router
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler

app = FastAPI(title="WorkflowSync API")

# Register global error handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "WorkflowSync backend is running"}
