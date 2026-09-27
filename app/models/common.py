from datetime import datetime, timezone


def utcnow() -> datetime:
    """Fecha actual en UTC con zona horaria (SQLModel la guarda y la devuelve en UTC)."""
    return datetime.now(timezone.utc)
