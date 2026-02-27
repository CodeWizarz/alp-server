from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Temporallayr"
    DATABASE_URL: str = ""  # Required in production; empty = DB unavailable
    API_KEY: str = "demo-key"
    TENANT: str = "demo-tenant"
    ENV: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
