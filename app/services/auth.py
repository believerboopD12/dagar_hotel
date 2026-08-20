"""Database-backed authentication and role authorization."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, UserRole
from app.utils.security import verify_password


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    username: str
    role: UserRole


def authenticate_user(
    session: Session, username: str, password: str, app_env: str = "development"
) -> AuthenticatedUser | None:
    user = session.scalar(
        select(User).where(User.username == username.strip().lower(), User.is_active.is_(True))
    )
    if user and app_env == "production" and user.is_demo:
        return None
    if not user or not verify_password(password, user.password_hash):
        return None
    return AuthenticatedUser(user.id, user.username, user.role)


def require_role(role: UserRole | str, *allowed: UserRole) -> None:
    normalized = role if isinstance(role, UserRole) else UserRole(role)
    if normalized not in allowed:
        raise PermissionError("You do not have permission to perform this action.")


ROLE_ACTIONS = {
    UserRole.ADMIN: {
        "dashboard",
        "counter_order",
        "orders",
        "customers_admin",
        "menu_admin",
    },
    UserRole.STAFF: {
        "dashboard",
        "counter_order",
        "orders",
        "customers_staff",
        "menu_view",
    },
}


def authorize_action(role: UserRole | str, action: str) -> None:
    normalized = role if isinstance(role, UserRole) else UserRole(role)
    if action not in ROLE_ACTIONS[normalized]:
        raise PermissionError("You do not have permission to access this area.")
