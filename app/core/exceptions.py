"""Excepciones de dominio.

Los servicios lanzan estas excepciones sin saber nada de HTTP; la capa API
(app/api/exception_handlers.py) las traduce al código de estado correspondiente.
"""


class AppError(Exception):
    default_message = "Error de la aplicación"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    default_message = "Recurso no encontrado"


class ConflictError(AppError):
    default_message = "Conflicto con datos existentes"


class InvalidDataError(AppError):
    default_message = "Datos inválidos"


class AuthenticationError(AppError):
    default_message = "Credenciales inválidas"


class PermissionDeniedError(AppError):
    default_message = "No tienes permisos para esta acción"


class AccountLockedError(AppError):
    default_message = "Cuenta bloqueada temporalmente por intentos fallidos"
