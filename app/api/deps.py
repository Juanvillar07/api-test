"""Inyección de dependencias de la capa API.

Aquí solo se extraen credenciales del request y se construyen los servicios;
toda decisión de negocio se delega a la capa de servicios.
"""
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie, APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import RolNombre, Usuario
from app.services.api_key_service import ApiKeyService
from app.services.auth_service import AuthService
from app.services.cliente_service import ClienteService
from app.services.usuario_service import UsuarioService

# ---------- Base de datos ----------

SessionDep = Annotated[Session, Depends(get_db)]


# ---------- Servicios ----------

def get_usuario_service(db: SessionDep) -> UsuarioService:
    return UsuarioService(db)


def get_auth_service(db: SessionDep) -> AuthService:
    return AuthService(db)


def get_api_key_service(db: SessionDep) -> ApiKeyService:
    return ApiKeyService(db)


def get_cliente_service(db: SessionDep) -> ClienteService:
    return ClienteService(db)


UsuarioServiceDep = Annotated[UsuarioService, Depends(get_usuario_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_api_key_service)]
ClienteServiceDep = Annotated[ClienteService, Depends(get_cliente_service)]


# ---------- Esquemas de seguridad (aparecen en Swagger) ----------

bearer_scheme = HTTPBearer(auto_error=False, description="JWT de acceso")
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False, description="API key")
session_scheme = APIKeyCookie(name=settings.session_cookie_name, auto_error=False, description="Cookie de sesión")

SessionCookie = Annotated[str | None, Depends(session_scheme)]


# ---------- Usuario actual y roles ----------

def get_current_user(
    auth: AuthServiceDep,
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    api_key: Annotated[str | None, Depends(api_key_scheme)],
    session_token: SessionCookie,
) -> Usuario:
    return auth.resolver_usuario(
        bearer_token=bearer.credentials if bearer else None,
        api_key=api_key,
        session_token=session_token,
    )


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_roles(*roles: RolNombre):
    def dependencia(usuario: CurrentUser) -> Usuario:
        AuthService.verificar_rol(usuario, roles)
        return usuario

    return dependencia


AdminUser = Annotated[Usuario, Depends(require_roles(RolNombre.ADMIN))]
