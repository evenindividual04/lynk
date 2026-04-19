from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///../data/lynk.db"
    cors_origins: str = "http://localhost:5173"

    # Claude API
    anthropic_api_key: str = ""
    claude_model_default: str = "claude-haiku-4-5-20251001"
    claude_model_high_priority: str = "claude-sonnet-4-6"

    # Email sending
    sending_enabled: bool = False
    gmail_user: str = ""
    gmail_app_password: str = ""

    # Tracking
    tracking_base_url: str = "http://localhost:8000"

    # Scheduler
    follow_up_scheduler_enabled: bool = True

    # Email finder API keys (empty = strategy skipped)
    hunter_api_key: str = ""
    apollo_api_key: str = ""
    skrapp_api_key: str = ""

    # Inbound IMAP polling
    inbound_polling_enabled: bool = True
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_verify_timeout_seconds: int = 8

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
