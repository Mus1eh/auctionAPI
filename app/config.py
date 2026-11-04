from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    sqlalchemy_url: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    reset_password_token_expire_minutes: int

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    frontend_url: str


# Kept apart so the API can start without the seed accounts' credentials.
class SeedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    superadmin_username: str
    superadmin_email: str
    superadmin_password: str

    admin_username: str
    admin_email: str
    admin_password: str

    seed_owner_username: str | None = None


settings = Settings()
