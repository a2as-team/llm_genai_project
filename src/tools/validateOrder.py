import json
from models import Order


async def validate_order(orderId: str, customerName: str) -> bool:
    """
    Validates an existing order.
    Parameters:
    - orderId: str - The ID of the order to validate
    Returns:
    - isValidated: bool - True if the order was validated successfully, False otherwise
    """
    isValidated = False

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
        order = Order.model_validate(order_data)
        if order.isValidated:
            print(f"Order with ID {orderId} is already validated.")
            return isValidated
    except FileNotFoundError:
        print(f"Order with ID {orderId} not found.")
        return isValidated

    # Validate the order - check that it has either formules or items
    if not order.formules and not order.items:
        print(f"Order with ID {orderId} is empty. Cannot validate.")
        return isValidated

    order.customerName = customerName
    order.isValidated = True
    isValidated = True

    # Save the updated order
    with open(f"orders/{orderId}.json", "w") as f:
        json.dump(order.model_dump(), f)

    return isValidated
