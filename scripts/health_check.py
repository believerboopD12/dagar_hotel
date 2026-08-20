"""Read-only and schema-level local application health checks."""

import importlib
import os
import sys

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

from app.config import PROJECT_ROOT, settings
from app.db.database import engine, initialize_database

REQUIRED_TABLES = {"customers", "menu_items", "orders", "order_items", "payments"}


def run() -> int:
    checks: list[tuple[str, bool, str]] = []
    try:
        settings.validate()
        checks.append(("Configuration", True, f"{settings.app_env} mode"))
    except Exception as exc:
        checks.append(("Configuration", False, str(exc)))
    for module in ("app.services.orders", "app.services.exports", "app.ui.pages"):
        try:
            importlib.import_module(module)
            checks.append((f"Import {module}", True, "available"))
        except Exception as exc:
            checks.append((f"Import {module}", False, str(exc)))
    data_directory = PROJECT_ROOT / "data"
    try:
        data_directory.mkdir(parents=True, exist_ok=True)
        writable = os.access(data_directory, os.W_OK)
        checks.append(("Data directory", writable, str(data_directory)))
    except OSError as exc:
        checks.append(("Data directory", False, str(exc)))
    try:
        initialize_database()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        missing = REQUIRED_TABLES - set(inspect(engine).get_table_names())
        checks.append(("Database connection", True, make_url(settings.sqlalchemy_url()).drivername))
        checks.append(
            (
                "Database schema",
                not missing,
                "all required tables exist" if not missing else f"missing: {sorted(missing)}",
            )
        )
    except Exception as exc:
        checks.append(("Database", False, str(exc)))
    auth_ok = settings.app_env != "production" or bool(settings.admin_password_hash)
    checks.append(
        (
            "Authentication",
            auth_ok,
            "appropriate for mode" if auth_ok else "production hash missing",
        )
    )
    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    return 0 if all(passed for _, passed, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(run())
