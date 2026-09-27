import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioRegistro(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe tener mayúsculas, minúsculas y números")
        return v


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nombre: str
    rol: str
    activo: bool
    creado_en: datetime

    @field_validator("rol", mode="before")
    @classmethod
    def extraer_nombre_rol(cls, v):
        # Acepta el objeto Rol de la relación o directamente el nombre
        return getattr(v, "nombre", v)
