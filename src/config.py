from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    database_url: str
    sentry_dsn: str | None = None
    redis_url: str
    jwt_secret: str
    jwt_algorithm: str
    # oauth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    # middleware
    middleware_secret: str
    frontend_url: str
    api_url: str
    # mail
    mail_username: str
    mail_password: SecretStr
    mail_port: int
    mail_server: str
    mail_from: str
    mail_from_name: str
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    use_credentials: bool = True
    validate_certs: bool = True
    email_secret: str
    password_reset_secret: str

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )


settings = Settings()  # type: ignore
