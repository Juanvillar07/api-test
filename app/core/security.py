import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

_hasher = PasswordHasher()  # Argon2id por defecto

# Hash usado para gastar el mismo tiempo cuando el email no existe (evita enumerar usuarios)
DUMMY_PASSWORD_HASH = _hasher.hash(secrets.token_urlsafe(16))


# ---------- Contraseñas ----------

def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# ---------- JWT ----------

def create_access_token(usuario_id: int, rol: str) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "role": rol,
        "type": "access",
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.access_token_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


# ---------- Tokens opacos (refresh, sesión, API key) ----------

def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Los tokens opacos solo se guardan hasheados; tienen suficiente entropía para usar SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Devuelve (key_completa, prefijo). El prefijo permite identificar la key sin revelarla."""
    prefijo = f"ak_{secrets.token_hex(4)}"
    return f"{prefijo}.{secrets.token_urlsafe(32)}", prefijo
