import json
from models import Order


async def remove_formule(
    orderId: str,
    formuleIndex: int,
) -> dict:
    """
    Removes a formule from an existing order.
    Parameters:
    - orderId: str - The ID of the order
    - formuleIndex: int - Index of the formule to remove (0 = first formule, 1 = second, etc.)

    Returns:
    - dict - Result with status, message, and updated formules list
    """
    result = {
        "success": False,
        "message": "",
        "formules": [],
    }

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
        order = Order.model_validate(order_data)
        if order.isValidated:
            result["message"] = (
                f"Order {orderId} is already validated. Cannot remove formules."
            )
            return result
    except FileNotFoundError:
        result["message"] = f"Order with ID {orderId} not found."
        return result

    # Check if formuleIndex is valid
    if formuleIndex < 0 or formuleIndex >= len(order.formules):
        result["message"] = (
            f"Formule index {formuleIndex} not found. Order has {len(order.formules)} formules."
        )
        return result

    # Remove the formule
    removed_formule = order.formules.pop(formuleIndex)

    # Save the updated order
    try:
        with open(f"orders/{orderId}.json", "w") as f:
            json.dump(order.model_dump(), f, indent=2)
        result["success"] = True
        result["formules"] = [
            {
                "formuleId": f.formuleId,
                "formuleName": f.formuleName,
                "quantity": f.quantity,
            }
            for f in order.formules
        ]
        result["message"] = (
            f"Successfully removed formule '{removed_formule.formuleName}' from order."
        )
    except Exception as e:
        result["message"] = f"Error saving order: {str(e)}"

    return result
