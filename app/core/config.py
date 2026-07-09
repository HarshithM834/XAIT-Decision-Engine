from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "XAIT Approval Decision Engine"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    DEV_MODE: bool = False

    # Security
    API_KEY: str
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_APP_ID_URI: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./data/decision_engine.db"

    # Config Files
    RULES_CONFIG_PATH: str = "config/rules.yaml"
    APP_CONFIG_PATH: str = "config/app.yaml"
    EMAIL_TEMPLATES_PATH: str = "config/email_templates.yaml"
    PAYLOAD_MAPPING_PATH: str = "config/payload_mapping.yaml"

    # Jobs (Email)
    SMTP_HOST: str = "mock"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "approvals@example.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
