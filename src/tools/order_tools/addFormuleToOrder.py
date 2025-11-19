import json
from pydantic import BaseModel
from src.models import Order, OrderFormule
from typing import List, Optional


class AddFormuleRequest(BaseModel):
    formuleId: str
    quantity: int = 1


async def add_formule_to_order(
    orderId: str,
    formules: List[dict],
) -> dict:
    """
    Adds one or multiple formules to an existing order.
    Parameters:
    - orderId: str - The ID of the order to which formules will be added
    - formules: List[dict] - List of formules to add, each containing:
        - formuleId: str - The ID of the formule (e.g., "form_001")
        - quantity: int - The quantity to add (optional, default 1)
        - items: List[dict] - Items for the formule (optional, but REQUIRED for validation). Each item:
            - itemId: str
            - quantity: int (optional, default 1)
            - indications: str (optional)
    Returns:
    - dict - Result with status, added count, and updated formules
    """
    result = {
        "success": False,
        "added_count": 0,
        "formules": [],
        "message": "",
        "errors": [],
    }

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
        order = Order.model_validate(order_data)
        if order.isValidated:
            result["message"] = (
                f"Order {orderId} is already validated. Cannot add formules."
            )
            return result
    except FileNotFoundError:
        result["message"] = f"Order with ID {orderId} not found."
        return result

    # Process each formule
    for formule_data in formules:
        # Convert dict to AddFormuleRequest object if needed
        if isinstance(formule_data, dict):
            formule_request = AddFormuleRequest.model_validate(formule_data)
        else:
            formule_request = formule_data

        # Check if formule exists in FORMULES by ID
        formule_template = None
        for key, f in FORMULES.items():
            if f.id == formule_request.formuleId:
                formule_template = f
                break

        if formule_template is None:
            error_msg = f"Formule with ID {formule_request.formuleId} not found."
            result["errors"].append(error_msg)
            continue

        # Check if items are provided (should be mandatory)
        items_to_add = formule_data.get("items", [])
        if not items_to_add:
            error_msg = f"Formule {formule_request.formuleId} requires items to be specified before adding."
            result["errors"].append(error_msg)
            continue

        # Add the formule to the order with provided items
        for _ in range(formule_request.quantity):
            # Create Item objects from the provided items
            formule_items = []
            for item_data in items_to_add:
                item = Item(
                    itemId=item_data["itemId"],
                    quantity=item_data.get("quantity", 1),
                    price=item_data.get("price", 0),
                    indications=item_data.get("indications", None),
                )
                formule_items.append(item)

            new_order_formule = OrderFormule(
                formuleId=formule_request.formuleId,
                formuleName=formule_template.name,
                formulaBasePrice=formule_template.price,
                items=formule_items,  # Filled with provided items
                quantity=1,
            )
            order.formules.append(new_order_formule)
            result["added_count"] += 1

    # Save the updated order
    try:
        with open(f"orders/{orderId}.json", "w") as f:
            json.dump(order.model_dump(), f, indent=2)
        result["success"] = True
        result["formules"] = [
            {
                "formuleId": f.formuleId,
                "formuleName": f.formuleName,
                "formulaBasePrice": f.formulaBasePrice,
                "quantity": f.quantity,
            }
            for f in order.formules
        ]
        result["message"] = f"Successfully added {result['added_count']} formule(s)."
    except Exception as e:
        result["message"] = f"Error saving order: {str(e)}"

    return result
