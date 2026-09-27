from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.models import RolNombre, Usuario
from app.schemas.usuario import UsuarioRegistro
from app.services.rol_service import RolService


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.roles = RolService(db)

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def obtener_por_email(self, email: str) -> Usuario | None:
        return self.db.exec(select(Usuario).where(Usuario.email == email.lower())).first()

    def existe(self, usuario_id: int) -> bool:
        return self.obtener_por_id(usuario_id) is not None

    def crear(self, email: str, nombre: str, password: str, rol: RolNombre) -> Usuario:
        if self.obtener_por_email(email):
            raise ConflictError("El email ya está registrado")

        usuario = Usuario(
            email=email.lower(),
            nombre=nombre,
            password_hash=hash_password(password),
            rol_id=self.roles.obtener_por_nombre(rol).id,
        )
        self.db.add(usuario)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("El email ya está registrado") from exc
        self.db.refresh(usuario)
        return usuario

    def registrar(self, datos: UsuarioRegistro) -> Usuario:
        """Registro público: siempre crea usuarios con rol cliente."""
        return self.crear(datos.email, datos.nombre, datos.password, RolNombre.CLIENTE)
