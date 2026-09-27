from fastapi import APIRouter

from app.api.v1.endpoints import api_keys, auth, clientes

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(api_keys.router)
api_router.include_router(clientes.router)
