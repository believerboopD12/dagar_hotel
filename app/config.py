"""Environment-based, local-first application configuration."""

import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "restaurant.db"


def _decimal_setting(name: str, default: str) -> Decimal:
    try:
        return Decimal(os.getenv(name, default))
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a valid number") from exc


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "").strip()
    app_env: str = os.getenv("APP_ENV", "development").lower()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    tax_rate: Decimal = _decimal_setting("TAX_RATE", "5")
    minimum_order_amount: Decimal = _decimal_setting("MINIMUM_ORDER_AMOUNT", "200")
    admin_password_hash: str = os.getenv("APP_ADMIN_PASSWORD_HASH", "")

    def sqlalchemy_url(self) -> str:
        """Return configured DB URL or the project-local SQLite fallback."""
        url = self.database_url or f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    def validate(self) -> None:
        if self.app_env not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be development, production, or test.")
        if not 0 <= self.tax_rate <= 100:
            raise ValueError("TAX_RATE must be between 0 and 100.")
        if self.minimum_order_amount < 0:
            raise ValueError("MINIMUM_ORDER_AMOUNT cannot be negative.")


settings = Settings()
