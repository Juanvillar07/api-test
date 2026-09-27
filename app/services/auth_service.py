from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta

from sqlmodel import Session, select, update

from app.core.config import settings
from app.core.exceptions import AccountLockedError, AuthenticationError, PermissionDeniedError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    decode_access_token,
    generate_token,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, RolNombre, Sesion, Usuario
from app.models.common import utcnow
from app.schemas.auth import TokenPar
from app.services.api_key_service import ApiKeyService
from app.services.usuario_service import UsuarioService


@dataclass(frozen=True)
class SesionCreada:
    usuario: Usuario
    token: str
    max_age: int  # segundos


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.usuarios = UsuarioService(db)
        self.api_keys = ApiKeyService(db)

    # ---------- Credenciales ----------

    def autenticar(self, email: str, password: str) -> Usuario:
        usuario = self.usuarios.obtener_por_email(email)
        ahora = utcnow()

        if usuario is None:
            verify_password(DUMMY_PASSWORD_HASH, password)  # tiempo constante: evita enumerar emails
            raise AuthenticationError()

        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
            raise AccountLockedError()

        if not verify_password(usuario.password_hash, password):
            self._registrar_intento_fallido(usuario)
            raise AuthenticationError()

        if not usuario.activo:
            raise PermissionDeniedError("Usuario inactivo")

        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def _registrar_intento_fallido(self, usuario: Usuario) -> None:
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= settings.max_failed_logins:
            usuario.bloqueado_hasta = utcnow() + timedelta(minutes=settings.lockout_minutes)
            usuario.intentos_fallidos = 0
        self.db.add(usuario)
        self.db.commit()

    # ---------- 1) JWT + refresh token con rotación ----------

    def login(self, email: str, password: str) -> TokenPar:
        return self._emitir_tokens(self.autenticar(email, password))

    def refrescar(self, refresh_token: str) -> TokenPar:
        registro = self._buscar_refresh(refresh_token)
        if registro is None:
            raise AuthenticationError()

        if registro.revocado:
            # Reutilización de un token ya rotado: posible robo -> se revocan todos los del usuario
            self.db.exec(
                update(RefreshToken)
                .where(RefreshToken.usuario_id == registro.usuario_id)
                .values(revocado=True)
            )
            self.db.commit()
            raise AuthenticationError()

        usuario = self.usuarios.obtener_por_id(registro.usuario_id)
        if registro.expira_en <= utcnow() or usuario is None or not usuario.activo:
            raise AuthenticationError()

        registro.revocado = True
        self.db.add(registro)
        self.db.commit()
        return self._emitir_tokens(usuario)

    def logout(self, refresh_token: str) -> None:
        registro = self._buscar_refresh(refresh_token)
        if registro and not registro.revocado:
            registro.revocado = True
            self.db.add(registro)
            self.db.commit()

    def _buscar_refresh(self, refresh_token: str) -> RefreshToken | None:
        return self.db.exec(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
        ).first()

    def _emitir_tokens(self, usuario: Usuario) -> TokenPar:
        refresh = generate_token()
        self.db.add(
            RefreshToken(
                usuario_id=usuario.id,
                token_hash=hash_token(refresh),
                expira_en=utcnow() + timedelta(days=settings.refresh_token_days),
            )
        )
        self.db.commit()
        return TokenPar(
            access_token=create_access_token(usuario.id, usuario.rol.nombre),
            refresh_token=refresh,
            expires_in=settings.access_token_minutes * 60,
        )

    # ---------- 2) Sesión con cookie ----------

    def iniciar_sesion(self, email: str, password: str) -> SesionCreada:
        usuario = self.autenticar(email, password)
        token = generate_token()
        self.db.add(
            Sesion(
                usuario_id=usuario.id,
                token_hash=hash_token(token),
                expira_en=utcnow() + timedelta(hours=settings.session_hours),
            )
        )
        self.db.commit()
        return SesionCreada(usuario=usuario, token=token, max_age=settings.session_hours * 3600)

    def cerrar_sesion(self, token: str | None) -> None:
        if not token:
            return
        sesion = self._buscar_sesion(token)
        if sesion and not sesion.revocado:
            sesion.revocado = True
            self.db.add(sesion)
            self.db.commit()

    def _buscar_sesion(self, token: str) -> Sesion | None:
        return self.db.exec(select(Sesion).where(Sesion.token_hash == hash_token(token))).first()

    # ---------- Resolución del usuario actual (los 3 métodos) ----------

    def resolver_usuario(
        self,
        bearer_token: str | None = None,
        api_key: str | None = None,
        session_token: str | None = None,
    ) -> Usuario:
        """Identifica al usuario por, en este orden: Bearer JWT, API key o cookie de sesión."""
        usuario_id: int | None = None

        if bearer_token:
            payload = decode_access_token(bearer_token)
            usuario_id = int(payload["sub"]) if payload else None
        elif api_key:
            usuario_id = self.api_keys.obtener_usuario_id(api_key)
        elif session_token:
            sesion = self._buscar_sesion(session_token)
            if sesion and not sesion.revocado and sesion.expira_en > utcnow():
                usuario_id = sesion.usuario_id

        usuario = self.usuarios.obtener_por_id(usuario_id) if usuario_id else None
        if usuario is None or not usuario.activo:
            raise AuthenticationError("No autenticado o credenciales inválidas")
        return usuario

    @staticmethod
    def verificar_rol(usuario: Usuario, roles_permitidos: Iterable[RolNombre]) -> None:
        if usuario.rol.nombre not in set(roles_permitidos):
            raise PermissionDeniedError()
