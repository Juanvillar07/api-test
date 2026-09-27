import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AccountLockedError,
    AppError,
    AuthenticationError,
    ConflictError,
    InvalidDataError,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

STATUS_POR_ERROR: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidDataError: status.HTTP_400_BAD_REQUEST,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    AccountLockedError: status.HTTP_423_LOCKED,
}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    codigo = next(
        (c for tipo, c in STATUS_POR_ERROR.items() if isinstance(exc, tipo)),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return JSONResponse(status_code=codigo, content={"detail": exc.message}, headers=headers)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Nunca se exponen detalles internos al cliente; quedan en el log
    logger.exception("Error no controlado en %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
