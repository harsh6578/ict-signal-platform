from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ICT Trading Signal Platform"
    environment: str = "development"
    database_url: str = "postgresql://ict_admin:ict_dev_password_change_me@localhost:5432/ict_signal_platform"

    binance_api_key: str = ""
    binance_api_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()