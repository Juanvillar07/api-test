from dataclasses import dataclass
from datetime import timedelta
from typing import Sequence

from sqlmodel import Session, select

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.security import generate_api_key, hash_token
from app.models import ApiKey
from app.models.common import utcnow
from app.schemas.api_key import ApiKeyCrear


@dataclass(frozen=True)
class ApiKeyGenerada:
    registro: ApiKey
    key: str  # valor en claro; solo existe en este momento


class ApiKeyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def crear(self, usuario_id: int, datos: ApiKeyCrear) -> ApiKeyGenerada:
        key, prefijo = generate_api_key()
        dias = datos.dias_validez or settings.api_key_days
        registro = ApiKey(
            usuario_id=usuario_id,
            nombre=datos.nombre,
            prefijo=prefijo,
            key_hash=hash_token(key),
            expira_en=utcnow() + timedelta(days=dias),
        )
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return ApiKeyGenerada(registro=registro, key=key)

    def listar(self, usuario_id: int) -> Sequence[ApiKey]:
        return self.db.exec(
            select(ApiKey).where(ApiKey.usuario_id == usuario_id).order_by(ApiKey.creado_en.desc())
        ).all()

    def revocar(self, usuario_id: int, api_key_id: int) -> None:
        registro = self.db.get(ApiKey, api_key_id)
        # Una key ajena se trata como inexistente para no revelar su existencia
        if registro is None or registro.usuario_id != usuario_id:
            raise NotFoundError("API key no encontrada")
        registro.revocado = True
        self.db.add(registro)
        self.db.commit()

    def obtener_usuario_id(self, key: str) -> int | None:
        """Valida una key y devuelve el id de su dueño, registrando el último uso."""
        registro = self.db.exec(select(ApiKey).where(ApiKey.key_hash == hash_token(key))).first()
        ahora = utcnow()
        if registro is None or registro.revocado or registro.expira_en <= ahora:
            return None
        registro.ultimo_uso = ahora
        self.db.add(registro)
        self.db.commit()
        return registro.usuario_id
