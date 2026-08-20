"""Restore a local SQLite backup with explicit confirmation."""

import argparse
import shutil
from pathlib import Path

from scripts.backup_db import sqlite_database_path


def restore_backup(backup: Path, destination: Path | None = None, confirm: bool = False) -> Path:
    if not confirm:
        raise ValueError("Restore requires explicit confirmation.")
    backup = backup.resolve()
    destination = (destination or sqlite_database_path()).resolve()
    if not backup.is_file():
        raise FileNotFoundError(f"Backup does not exist: {backup}")
    if backup.suffix.lower() != ".db":
        raise ValueError("Backup must be a .db file.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, destination)
    print(f"Database restored: {destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument(
        "--confirm", action="store_true", help="Allow overwriting the local database"
    )
    args = parser.parse_args()
    restore_backup(args.backup, confirm=args.confirm)


if __name__ == "__main__":
    main()
