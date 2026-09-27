from enum import StrEnum

from sqlmodel import Field, SQLModel


class RolNombre(StrEnum):
    ADMIN = "admin"
    CLIENTE = "cliente"


class Rol(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)
