from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Aplicación ---
    app_name: str = "API Test"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: list[str] = []

    # --- Base de datos ---
    mysql_host: str = "db"
    mysql_port: int = 3306
    mysql_user: str
    mysql_password: str
    mysql_database: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # --- JWT ---
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    # --- Sesiones con cookie ---
    session_hours: int = 8
    session_cookie_name: str = "session_id"
    cookie_secure: bool = True

    # --- API keys ---
    api_key_days: int = 90

    # --- Bloqueo de cuenta ---
    max_failed_logins: int = 5
    lockout_minutes: int = 15

    # --- Administrador inicial ---
    admin_email: str
    admin_password: str
    admin_nombre: str = "Administrador"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{quote_plus(self.mysql_user)}:{quote_plus(self.mysql_password)}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
