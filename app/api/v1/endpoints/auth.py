from fastapi import APIRouter, Response, status

from app.api.deps import AuthServiceDep, CurrentUser, SessionCookie, UsuarioServiceDep
from app.core.config import settings
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPar
from app.schemas.usuario import UsuarioPublico, UsuarioRegistro

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def registrar(datos: UsuarioRegistro, usuarios: UsuarioServiceDep):
    return UsuarioPublico.model_validate(usuarios.registrar(datos))


@router.get("/me", response_model=UsuarioPublico)
def me(usuario: CurrentUser):
    return UsuarioPublico.model_validate(usuario)


# ---------- 1) JWT ----------

@router.post("/login", response_model=TokenPar)
def login(datos: LoginRequest, auth: AuthServiceDep):
    return auth.login(datos.email, datos.password)


@router.post("/refresh", response_model=TokenPar)
def refrescar(datos: RefreshRequest, auth: AuthServiceDep):
    return auth.refrescar(datos.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(datos: RefreshRequest, auth: AuthServiceDep):
    auth.logout(datos.refresh_token)


# ---------- 2) Sesión con cookie ----------

@router.post("/session/login", response_model=UsuarioPublico)
def login_sesion(datos: LoginRequest, response: Response, auth: AuthServiceDep):
    sesion = auth.iniciar_sesion(datos.email, datos.password)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=sesion.token,
        max_age=sesion.max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return UsuarioPublico.model_validate(sesion.usuario)


@router.post("/session/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_sesion(response: Response, session_token: SessionCookie, auth: AuthServiceDep):
    auth.cerrar_sesion(session_token)
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )
