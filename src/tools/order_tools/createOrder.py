from uuid import uuid4
import json
from src.models import Order


async def create_order():
    """
    Creates a new order and returns the order ID.
    """
    order_id = uuid4()
    order = Order(
        orderId=order_id, customerName=None, formules=[], items=[], isValidated=False
    )
    # save order_data in the folder 'orders' as a json file
    with open(f"orders/{order_id}.json", "w") as f:
        json.dump(order_data, f)
    return order_id
