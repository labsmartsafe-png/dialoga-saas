from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "chave-padrao-desenvolvimento-troque-em-producao-64-caracteres-min"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 43200
    database_url: str = "sqlite:///./data/dialoga.db"
    cors_origins: str = "http://localhost:3000,http://localhost:8000,http://localhost:5500,http://127.0.0.1:5500,http://127.0.0.1:8000"
    host: str = "0.0.0.0"
    port: int = 8000
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_verify_token: str = "dialoga-verify"
    max_upload_mb: int = 10
    rate_limit_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
