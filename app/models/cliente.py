from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.common import utcnow


class Cliente(SQLModel, table=True):
    __tablename__ = "clientes"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    documento: str = Field(max_length=30, unique=True, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)
    usuario_id: int | None = Field(default=None, foreign_key="usuarios.id")
    creado_por: int = Field(foreign_key="usuarios.id")
    creado_en: datetime = Field(default_factory=utcnow)
    actualizado_en: datetime = Field(default_factory=utcnow, sa_column_kwargs={"onupdate": utcnow})
