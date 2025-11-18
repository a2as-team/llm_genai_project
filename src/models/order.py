from pydantic import BaseModel, Field
from typing import Optional, List


class Item(BaseModel):
    itemId: str
    quantity: int = 1
    price: float
    indications: Optional[str] = Field(None, description="par exemple: 'sans oignons'")


class Formule(BaseModel):
    """Classe de base pour toutes les formules"""

    id: str
    name: str
    price: float
    description: str
    items: List[Item] = Field(default_factory=list)


class OrderFormule(BaseModel):
    """Une formule dans une commande - peut être modifiée indépendamment"""

    formuleId: str  # Référence à la formule (ex: "form_001")
    formuleName: str  # Nom de la formule à la commande
    formulaBasePrice: float  # Prix de base de la formule
    items: List[Item] = Field(
        default_factory=list
    )  # Items actuels (peuvent être modifiés)
    quantity: int = 1  # Nombre de fois cette formule est commandée


class Order(BaseModel):
    orderId: str
    customerName: Optional[str] = None
    formules: List[OrderFormule] = Field(default_factory=list)  # Formules commandées
    items: List[Item] = Field(default_factory=list)  # Items individuels (non-formule)
    isValidated: bool = False


# Instances de formules prédéfinies
FORMULES = {
    "enfant": Formule(
        id="form_001",
        name="Formule Enfant",
        price=9.50,
        description="1 pizza enfant (petite), 1 boisson, 1 dessert",
    ),
    "classique": Formule(
        id="form_002",
        name="Formule Classique",
        price=16.50,
        description="1 plat au choix, 1 entrée, 1 boisson",
    ),
    "gourmande": Formule(
        id="form_003",
        name="Formule Gourmande",
        price=22.00,
        description="1 entrée, 1 plat, 1 dessert, 1 boisson",
    ),
    "duet": Formule(
        id="form_004",
        name="Formule Duo (2 personnes)",
        price=35.00,
        description="2 pizzas différentes, 1 entrée à partager, 2 boissons",
    ),
    "trio": Formule(
        id="form_005",
        name="Formule Trio (3 personnes)",
        price=50.00,
        description="3 pizzas différentes, 2 entrées à partager, 3 boissons, 1 dessert à partager",
    ),
    "famille": Formule(
        id="form_006",
        name="Formule Famille (4 personnes)",
        price=65.00,
        description="4 pizzas différentes, 2 entrées, 4 boissons, 2 desserts",
    ),
    "vegetarienne": Formule(
        id="form_007",
        name="Formule Végétarienne",
        price=18.00,
        description="1 plat végétarien, 1 entrée végétarienne, 1 boisson, 1 dessert",
    ),
    "affaires": Formule(
        id="form_008",
        name="Menu Affaires (déjeuner rapide)",
        price=12.50,
        description="1 pizza médium, 1 boisson (eau, café ou soda)",
    ),
}
