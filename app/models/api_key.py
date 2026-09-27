from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.common import utcnow


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)
    nombre: str = Field(max_length=100)
    prefijo: str = Field(max_length=16, index=True)
    key_hash: str = Field(max_length=64, unique=True, index=True)
    expira_en: datetime
    revocado: bool = Field(default=False)
    ultimo_uso: datetime | None = Field(default=None)
    creado_en: datetime = Field(default_factory=utcnow)
