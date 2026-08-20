"""Portable menu-image resolution with category fallbacks."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = PROJECT_ROOT / "assets"

ITEM_IMAGES = {
    "Tea": "chai.jpg",
    "Cold Drink": "coc.jpg",
    "Dahi": "dahi.jpg",
    "Dal Tadka (Half)": "dal.jpg",
    "Dal Tadka (Full)": "dal.jpg",
    "Paratha": "prntha.jpg",
    "Sada Roti": "roti.jpg",
    "Tandoori Roti": "tndroti.jpg",
    "Shahi Paneer (Half)": "shipnr.jpg",
    "Shahi Paneer (Full)": "shipnr.jpg",
    "Matar Mushroom (Half)": "sahipnr_re.jpg",
    "Matar Mushroom (Full)": "sahipnr_re.jpg",
}
CATEGORY_FALLBACKS = {
    "Curries": "menu/generic-curry.webp",
    "Bread": "menu/generic-bread.webp",
    "Sides & Drinks": "menu/generic-sides-drinks.webp",
}
DEFAULT_FALLBACK = "menu/generic-sides-drinks.webp"


def resolve_menu_image(item_name: str, category: str) -> Path:
    relative = ITEM_IMAGES.get(item_name, CATEGORY_FALLBACKS.get(category, DEFAULT_FALLBACK))
    candidate = (ASSET_ROOT / relative).resolve()
    if candidate.is_file() and ASSET_ROOT in candidate.parents:
        return candidate
    return (ASSET_ROOT / DEFAULT_FALLBACK).resolve()
