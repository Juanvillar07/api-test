from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, ClienteServiceDep
from app.schemas.cliente import ClienteActualizar, ClienteCrear, ClientePublico
from app.schemas.common import Pagina

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClientePublico, status_code=status.HTTP_201_CREATED)
def crear_cliente(datos: ClienteCrear, admin: AdminUser, clientes: ClienteServiceDep):
    return clientes.crear(datos, creado_por=admin.id)


@router.get("", response_model=Pagina[ClientePublico])
def listar_clientes(
    _: AdminUser,
    clientes: ClienteServiceDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    buscar: Annotated[str | None, Query(max_length=100, description="Nombre, apellido, documento o email")] = None,
):
    return clientes.listar(offset=offset, limit=limit, buscar=buscar)


@router.get("/{cliente_id}", response_model=ClientePublico)
def obtener_cliente(cliente_id: int, _: AdminUser, clientes: ClienteServiceDep):
    return clientes.obtener(cliente_id)


@router.put("/{cliente_id}", response_model=ClientePublico)
def actualizar_cliente(cliente_id: int, datos: ClienteActualizar, _: AdminUser, clientes: ClienteServiceDep):
    return clientes.actualizar(cliente_id, datos)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, _: AdminUser, clientes: ClienteServiceDep):
    clientes.eliminar(cliente_id)
