from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.common import utcnow


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)
    token_hash: str = Field(max_length=64, unique=True, index=True)
    expira_en: datetime
    revocado: bool = Field(default=False)
    creado_en: datetime = Field(default_factory=utcnow)
