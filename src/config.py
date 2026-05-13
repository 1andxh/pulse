from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )


settings = Settings()  # type: ignore
