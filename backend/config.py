from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    firebase_project_id: str = "bookmyseat-8d477"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
