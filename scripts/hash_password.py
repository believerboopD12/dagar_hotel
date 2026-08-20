"""Generate a value for APP_ADMIN_PASSWORD_HASH without storing the password."""

from getpass import getpass

from app.utils.security import hash_password

if __name__ == "__main__":
    print(hash_password(getpass("New admin password: ")))
