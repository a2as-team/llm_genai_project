import json
from models import Order


async def get_price(orderId: str) -> float:
    """
    Calculates the total price of an order.
    Parameters:
    - orderId: str - The ID of the order
    Returns:
    - total_price: float - The total price of the order
    """
    total_price = 0.0

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
    except FileNotFoundError:
        print(f"Order with ID {orderId} not found.")
        return total_price

    order = Order.model_validate(order_data)
    for order_item in order.items:
        total_price += order_item.price * order_item.quantity

    return total_price
