RESTAURANT_PROFILE = {
    "name": "Pizza Royal",
    "address": "2 bis Avenue Foch, 75016 Paris",
    "metro": "Étoile (lignes 1, 2, 6)",
    "rer": "Charles de Gaulle - Étoile (RER A)",
    "parking": "Parking Vinci Park à 100m, Avenue Foch",
    "phone_number": "+33 1 45 23 98 76",
    "website": "https://pizzaroyal.fr",
    "opening_hours": {
        "lunch": "11h30 - 14h30",
        "dinner": "18h30 - 23h00",
        "open_days": "Tous les jours"
    },
    "cuisine": "Italienne et pizzeria traditionnelle",
    "specialties": [
        "Pizza Regina au feu de bois",
        "Burrata crémeuse",
        "Tiramisu maison"
    ],
    "terrace": True,
    "takeaway": True,
    "delivery": True,
    "child_friendly": True,
    "pets_allowed": False,
    "payment_methods": ["Carte bancaire", "Espèces", "Tickets restaurant"],
    "ambiance": "Chaleureuse, idéale pour un dîner entre amis ou en famille",
    "accessibility": "Accessible aux personnes à mobilité réduite"
}

async def get_informations() -> dict:
    return RESTAURANT_PROFILE