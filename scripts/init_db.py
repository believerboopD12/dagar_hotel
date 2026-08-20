"""Create all database tables."""

from app.db.database import initialize_database

if __name__ == "__main__":
    initialize_database()
    print("Database schema is ready.")
