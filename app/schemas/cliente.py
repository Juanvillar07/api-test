from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class _NormalizaEmail(BaseModel):
    @field_validator("email", check_fields=False)
    @classmethod
    def normalizar_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v


class ClienteCrear(_NormalizaEmail):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    documento: str = Field(min_length=3, max_length=30)
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)
    usuario_id: int | None = None


class ClienteActualizar(_NormalizaEmail):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    documento: str | None = Field(default=None, min_length=3, max_length=30)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=255)
    usuario_id: int | None = None


class ClientePublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    documento: str
    email: str
    telefono: str | None
    direccion: str | None
    usuario_id: int | None
    creado_por: int
    creado_en: datetime
    actualizado_en: datetime
