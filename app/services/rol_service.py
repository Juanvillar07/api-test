from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models import Rol, RolNombre

ROLES_BASE: dict[RolNombre, str] = {
    RolNombre.ADMIN: "Administrador del sistema",
    RolNombre.CLIENTE: "Cliente de la aplicación",
}


class RolService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_por_nombre(self, nombre: RolNombre) -> Rol:
        rol = self.db.exec(select(Rol).where(Rol.nombre == nombre)).first()
        if rol is None:
            raise NotFoundError(f"Rol '{nombre}' no encontrado")
        return rol

    def asegurar_roles_base(self) -> None:
        existentes = set(self.db.exec(select(Rol.nombre)).all())
        for nombre, descripcion in ROLES_BASE.items():
            if nombre not in existentes:
                self.db.add(Rol(nombre=nombre, descripcion=descripcion))
        self.db.commit()
