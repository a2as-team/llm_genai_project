import json
from models import Order


async def get_current_order(orderId: str) -> dict:
    """
    Retrieves the current order details including formules and items.
    Parameters:
    - orderId: str - The ID of the order
    Returns:
    - dict - Order details including orderId, customerName, formules, items, isValidated, and total_price
    """
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)

        # Validate and format order data
        order = Order.model_validate(order_data)

        # Calculate total price from formules and items
        formule_price = sum(f.formulaBasePrice * f.quantity for f in order.formules)
        items_price = sum(item.price * item.quantity for item in order.items)
        total_price = formule_price + items_price

        return {
            "orderId": order.orderId,
            "customerName": order.customerName,
            "formules": [
                {
                    "formuleId": f.formuleId,
                    "formuleName": f.formuleName,
                    "formulaBasePrice": f.formulaBasePrice,
                    "quantity": f.quantity,
                    "items": [
                        {
                            "itemId": item.itemId,
                            "quantity": item.quantity,
                            "price": item.price,
                            "indications": item.indications,
                        }
                        for item in f.items
                    ],
                }
                for f in order.formules
            ],
            "items": [
                {
                    "itemId": item.itemId,
                    "quantity": item.quantity,
                    "price": item.price,
                    "indications": item.indications,
                    "subtotal": item.price * item.quantity,
                }
                for item in order.items
            ],
            "total_price": total_price,
            "isValidated": order.isValidated,
        }
    except FileNotFoundError:
        return {"error": f"Order with ID {orderId} not found."}
    except Exception as e:
        return {"error": f"Error retrieving order: {str(e)}"}
