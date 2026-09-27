import logging

from sqlmodel import Session, SQLModel

from app.core.config import settings
from app.db.session import engine
from app.models.rol import RolNombre
from app.services.rol_service import RolService
from app.services.usuario_service import UsuarioService

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Crea las tablas y los datos base (roles + administrador inicial)."""
    import app.models  # noqa: F401  registra los modelos en la metadata

    SQLModel.metadata.create_all(engine)

    with Session(engine) as db:
        RolService(db).asegurar_roles_base()

        usuarios = UsuarioService(db)
        if usuarios.obtener_por_email(settings.admin_email) is None:
            usuarios.crear(
                email=settings.admin_email,
                nombre=settings.admin_nombre,
                password=settings.admin_password,
                rol=RolNombre.ADMIN,
            )
            logger.info("Administrador inicial creado")
