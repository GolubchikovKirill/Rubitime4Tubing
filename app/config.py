from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_MODE: str = "webhook"

    BOT_TOKEN: str
    BASE_URL: str
    WEBHOOK_PATH: str = "/tg/webhook"
    WEBHOOK_SECRET: str = ""

    OPERATOR_IDS: str = ""

    DB_URL: str
    REDIS_URL: str = "redis://redis:6379/0"

    WEBAPP_SCANNER_PATH: str = "/webapp/scanner"

    def operator_id_set(self) -> set[int]:
        raw = (self.OPERATOR_IDS or "").strip()
        if not raw:
            return set()
        return {int(x.strip()) for x in raw.split(",") if x.strip()}

    @property
    def webhook_url(self) -> str:
        base = self.BASE_URL.rstrip("/")
        path = self.WEBHOOK_PATH if self.WEBHOOK_PATH.startswith("/") else f"/{self.WEBHOOK_PATH}"
        return f"{base}{path}"

    @property
    def webapp_scanner_url(self) -> str:
        base = self.BASE_URL.rstrip("/")
        path = self.WEBAPP_SCANNER_PATH if self.WEBAPP_SCANNER_PATH.startswith("/") else f"/{self.WEBAPP_SCANNER_PATH}"
        return f"{base}{path}"


settings = Settings()
