"""Original menu, converted from hard-coded UI data into seedable records."""

from decimal import Decimal

MENU_ITEMS = {
    "Curries": {
        "Matar Paneer (Half)": 70,
        "Matar Paneer (Full)": 130,
        "Kadhai Paneer (Half)": 100,
        "Kadhai Paneer (Full)": 180,
        "Mix Veg (Half)": 100,
        "Mix Veg (Full)": 180,
        "Shahi Paneer (Half)": 80,
        "Shahi Paneer (Full)": 150,
        "Butter Paneer Masala (Half)": 130,
        "Butter Paneer Masala (Full)": 230,
        "Paneer Bhurji (Half)": 180,
        "Paneer Bhurji (Full)": 300,
        "Matar Mushroom (Half)": 70,
        "Matar Mushroom (Full)": 130,
        "Sev Bhurji": 120,
        "Dal Makhani (Half)": 70,
        "Dal Makhani (Full)": 120,
        "Dal Tadka (Half)": 50,
        "Dal Tadka (Full)": 80,
        "Amritsari Chhole (Half)": 70,
        "Amritsari Chhole (Full)": 120,
        "Chana Masala": 180,
    },
    "Bread": {
        "Sada Roti": 10,
        "Butter Roti": 15,
        "Pyaz Roti": 15,
        "Butter Pyaz Roti": 20,
        "Missi Roti": 20,
        "Butter Missi Roti": 25,
        "Garlic Naan": 25,
        "Butter Garlic Naan": 30,
        "Butter Naan": 30,
        "Sada Naan": 20,
        "Aloo Naan": 30,
        "Butter Aloo Naan": 40,
        "Paneer Naan": 50,
        "Butter Paneer Naan": 60,
    },
    "Sides & Drinks": {
        "Raita": 50,
        "Dahi": 50,
        "Water Bottle": 20,
        "Cold Drink": 50,
        "Mix Salad": 30,
        "Green Salad": 60,
    },
}


def flattened_menu() -> list[tuple[str, str, Decimal]]:
    return [
        (name, category, Decimal(price))
        for category, entries in MENU_ITEMS.items()
        for name, price in entries.items()
    ]
