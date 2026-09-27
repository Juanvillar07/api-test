from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, or_, select

from app.core.exceptions import ConflictError, InvalidDataError, NotFoundError
from app.models import Cliente
from app.schemas.cliente import ClienteActualizar, ClienteCrear
from app.schemas.common import Pagina
from app.services.usuario_service import UsuarioService


class ClienteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.usuarios = UsuarioService(db)

    def obtener(self, cliente_id: int) -> Cliente:
        cliente = self.db.get(Cliente, cliente_id)
        if cliente is None:
            raise NotFoundError("Cliente no encontrado")
        return cliente

    def listar(self, offset: int, limit: int, buscar: str | None = None) -> Pagina[Cliente]:
        consulta = select(Cliente)
        if buscar:
            patron = f"%{buscar}%"
            consulta = consulta.where(
                or_(
                    Cliente.nombre.like(patron),
                    Cliente.apellido.like(patron),
                    Cliente.documento.like(patron),
                    Cliente.email.like(patron),
                )
            )
        total = self.db.exec(select(func.count()).select_from(consulta.subquery())).one()
        items = self.db.exec(consulta.order_by(Cliente.id).offset(offset).limit(limit)).all()
        return Pagina[Cliente](total=total, offset=offset, limit=limit, items=list(items))

    def crear(self, datos: ClienteCrear, creado_por: int) -> Cliente:
        self._validar_unicos(datos.documento, datos.email)
        self._validar_usuario(datos.usuario_id)
        cliente = Cliente(**datos.model_dump(), creado_por=creado_por)
        return self._guardar(cliente)

    def actualizar(self, cliente_id: int, datos: ClienteActualizar) -> Cliente:
        cliente = self.obtener(cliente_id)
        cambios = datos.model_dump(exclude_unset=True)
        self._validar_unicos(cambios.get("documento"), cambios.get("email"), excluir_id=cliente.id)
        self._validar_usuario(cambios.get("usuario_id"))
        cliente.sqlmodel_update(cambios)
        return self._guardar(cliente)

    def eliminar(self, cliente_id: int) -> None:
        cliente = self.obtener(cliente_id)
        self.db.delete(cliente)
        self.db.commit()

    # ---------- Reglas internas ----------

    def _validar_unicos(self, documento: str | None, email: str | None, excluir_id: int | None = None) -> None:
        condiciones = []
        if documento:
            condiciones.append(Cliente.documento == documento)
        if email:
            condiciones.append(Cliente.email == email)
        if not condiciones:
            return
        consulta = select(Cliente.id).where(or_(*condiciones))
        if excluir_id is not None:
            consulta = consulta.where(Cliente.id != excluir_id)
        if self.db.exec(consulta).first() is not None:
            raise ConflictError("Ya existe un cliente con ese documento o email")

    def _validar_usuario(self, usuario_id: int | None) -> None:
        if usuario_id is not None and not self.usuarios.existe(usuario_id):
            raise InvalidDataError("El usuario_id no existe")

    def _guardar(self, cliente: Cliente) -> Cliente:
        self.db.add(cliente)
        try:
            self.db.commit()
        except IntegrityError as exc:
            # Protección ante condiciones de carrera entre la validación y el insert
            self.db.rollback()
            raise ConflictError() from exc
        self.db.refresh(cliente)
        return cliente
