from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    dias_validez: int | None = Field(default=None, ge=1, le=365)


class ApiKeyPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    prefijo: str
    expira_en: datetime
    revocado: bool
    ultimo_uso: datetime | None
    creado_en: datetime


class ApiKeyCreada(ApiKeyPublica):
    key: str = Field(description="Solo se muestra una vez; guárdala en un lugar seguro")
