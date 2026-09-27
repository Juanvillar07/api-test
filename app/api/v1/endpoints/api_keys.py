from fastapi import APIRouter, status

from app.api.deps import ApiKeyServiceDep, CurrentUser
from app.schemas.api_key import ApiKeyCreada, ApiKeyCrear, ApiKeyPublica

# ---------- 3) API keys ----------

router = APIRouter(prefix="/auth/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreada, status_code=status.HTTP_201_CREATED)
def crear_api_key(datos: ApiKeyCrear, usuario: CurrentUser, api_keys: ApiKeyServiceDep):
    generada = api_keys.crear(usuario.id, datos)
    publica = ApiKeyPublica.model_validate(generada.registro)
    return ApiKeyCreada(**publica.model_dump(), key=generada.key)


@router.get("", response_model=list[ApiKeyPublica])
def listar_api_keys(usuario: CurrentUser, api_keys: ApiKeyServiceDep):
    return api_keys.listar(usuario.id)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revocar_api_key(api_key_id: int, usuario: CurrentUser, api_keys: ApiKeyServiceDep):
    api_keys.revocar(usuario.id, api_key_id)
