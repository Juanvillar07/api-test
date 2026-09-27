from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.common import utcnow
from app.models.rol import Rol


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    nombre: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    rol_id: int = Field(foreign_key="roles.id")
    activo: bool = Field(default=True)
    intentos_fallidos: int = Field(default=0)
    bloqueado_hasta: datetime | None = Field(default=None)
    creado_en: datetime = Field(default_factory=utcnow)
    actualizado_en: datetime = Field(default_factory=utcnow, sa_column_kwargs={"onupdate": utcnow})

    rol: Rol | None = Relationship(sa_relationship_kwargs={"lazy": "joined"})
