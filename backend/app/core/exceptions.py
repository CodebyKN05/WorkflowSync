from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class AppException(Exception):
    """
    Base application exception for expected API/business errors.
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle expected application errors with a stable JSON response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected errors.
    Returns a generic 500 without exposing internal details to the client.
    """
    # Log the real exception internally, but do not expose it
    logger.error(f"Unexpected error handling request {request.method} {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
