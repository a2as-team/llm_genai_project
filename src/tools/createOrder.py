from uuid import uuid4
import json
from models import Order


async def create_order():
    """
    Creates a new order and returns the order ID.
    """
    order_id = str(uuid4())
    order_data = Order(
        orderId=order_id, customerName=None, formules=[], items=[], isValidated=False
    ).model_dump()
    # save order_data in the folder 'orders' as a json file
    with open(f"orders/{order_id}.json", "w") as f:
        json.dump(order_data, f)
    return order_id
