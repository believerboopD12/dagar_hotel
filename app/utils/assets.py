"""Portable menu-image resolution with category fallbacks."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = PROJECT_ROOT / "assets"

ITEM_IMAGES = {
    "Tea": "chai.jpg",
    "Cold Drink": "menu/dishes/cold-drink.webp",
    "Dahi": "menu/dishes/dahi.webp",
    "Dal Tadka (Half)": "menu/dishes/dal-tadka.webp",
    "Dal Tadka (Full)": "menu/dishes/dal-tadka.webp",
    "Paratha": "prntha.jpg",
    "Sada Roti": "menu/dishes/sada-roti.webp",
    "Butter Roti": "menu/dishes/sada-roti.webp",
    "Tandoori Roti": "tndroti.jpg",
    "Shahi Paneer (Half)": "menu/dishes/shahi-paneer.webp",
    "Shahi Paneer (Full)": "menu/dishes/shahi-paneer.webp",
    "Matar Mushroom (Half)": "menu/dishes/matar-mushroom.webp",
    "Matar Mushroom (Full)": "menu/dishes/matar-mushroom.webp",
    "Matar Paneer (Half)": "menu/dishes/matar-paneer.webp",
    "Matar Paneer (Full)": "menu/dishes/matar-paneer.webp",
    "Kadhai Paneer (Half)": "menu/dishes/kadhai-paneer.webp",
    "Kadhai Paneer (Full)": "menu/dishes/kadhai-paneer.webp",
    "Mix Veg (Half)": "menu/dishes/mix-veg.webp",
    "Mix Veg (Full)": "menu/dishes/mix-veg.webp",
    "Butter Paneer Masala (Half)": "menu/dishes/butter-paneer-masala.webp",
    "Butter Paneer Masala (Full)": "menu/dishes/butter-paneer-masala.webp",
    "Paneer Bhurji (Half)": "menu/dishes/paneer-bhurji.webp",
    "Paneer Bhurji (Full)": "menu/dishes/paneer-bhurji.webp",
    "Sev Bhurji": "menu/dishes/sev-bhurji.webp",
    "Dal Makhani (Half)": "menu/dishes/dal-makhani.webp",
    "Dal Makhani (Full)": "menu/dishes/dal-makhani.webp",
    "Amritsari Chhole (Half)": "menu/dishes/amritsari-chhole.webp",
    "Amritsari Chhole (Full)": "menu/dishes/amritsari-chhole.webp",
    "Chana Masala": "menu/dishes/chana-masala.webp",
    "Pyaz Roti": "menu/dishes/pyaz-roti.webp",
    "Butter Pyaz Roti": "menu/dishes/pyaz-roti.webp",
    "Missi Roti": "menu/dishes/missi-roti.webp",
    "Butter Missi Roti": "menu/dishes/missi-roti.webp",
    "Garlic Naan": "menu/dishes/garlic-naan.webp",
    "Butter Garlic Naan": "menu/dishes/garlic-naan.webp",
    "Sada Naan": "menu/dishes/plain-naan.webp",
    "Butter Naan": "menu/dishes/plain-naan.webp",
    "Aloo Naan": "menu/dishes/aloo-naan.webp",
    "Butter Aloo Naan": "menu/dishes/aloo-naan.webp",
    "Paneer Naan": "menu/dishes/paneer-naan.webp",
    "Butter Paneer Naan": "menu/dishes/paneer-naan.webp",
    "Raita": "menu/dishes/raita.webp",
    "Water Bottle": "menu/dishes/water-bottle.webp",
    "Mix Salad": "menu/dishes/salad.webp",
    "Green Salad": "menu/dishes/salad.webp",
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
