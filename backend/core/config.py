from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ICT Trading Signal Platform"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()