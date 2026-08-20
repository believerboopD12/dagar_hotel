"""Create a safe, timestamped backup of the local SQLite database."""

import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from app.config import PROJECT_ROOT, settings


def sqlite_database_path(database_url: str | None = None) -> Path:
    url = make_url(database_url or settings.sqlalchemy_url())
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        raise ValueError("Backup is available only for a file-based SQLite database.")
    return Path(url.database).resolve()


def create_backup(
    source: Path | None = None, backup_directory: Path | None = None, now: datetime | None = None
) -> Path:
    source = (source or sqlite_database_path()).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Database does not exist: {source}")
    backup_directory = (backup_directory or PROJECT_ROOT / "backups").resolve()
    backup_directory.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H%M%S_%f")
    destination = backup_directory / f"restaurant_{stamp}.db"
    shutil.copy2(source, destination)
    print(f"Backup created: {destination}")
    return destination


if __name__ == "__main__":
    create_backup()
