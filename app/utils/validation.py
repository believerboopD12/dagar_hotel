"""Input validation shared by UI and services."""

import re

PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def clean_name(value: str) -> str:
    name = " ".join(value.strip().split())
    if not 2 <= len(name) <= 100:
        raise ValueError("Name must contain between 2 and 100 characters.")
    return name


def validate_phone(value: str) -> str:
    phone = re.sub(r"[\s-]", "", value)
    if not PHONE_PATTERN.fullmatch(phone):
        raise ValueError("Enter a valid 10-digit Indian mobile number.")
    return phone


def validate_email(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    email = value.strip().lower()
    if len(email) > 255 or not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Enter a valid email address.")
    return email
