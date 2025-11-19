import json
import pandas as pd
from pydantic import BaseModel
from src.models import Order
from typing import List, Optional


class AddItemRequest(BaseModel):
    itemId: str
    quantity: int
    indications: Optional[str] = None


def get_price_from_db(item_id: str) -> Optional[float]:
    """Retrieve price from db.csv based on item ID."""
    try:
        df = pd.read_csv("db.csv")
        row = df[df["id"] == item_id]
        if not row.empty:
            return float(row.iloc[0]["prix"])
    except Exception as e:
        print(f"Error reading price from db.csv: {e}")
    return None


async def add_item_to_order(
    orderId: str,
    items: List[AddItemRequest],
) -> dict:
    """
    Adds one or multiple items to an existing order.
    Parameters:
    - orderId: str - The ID of the order to which items will be added
    - items: List[AddItemRequest] - List of items to add, each containing:
        - itemId: str - The ID of the item
        - quantity: int - The quantity to add
        - indications: Optional[str] - Optional indications (e.g., "sans oignons")
    Returns:
    - dict - Result with status, added count, and updated items
    """
    result = {
        "success": False,
        "added_count": 0,
        "updated_count": 0,
        "items": [],
        "message": "",
    }

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
        order = Order.model_validate(order_data)
        if order.isValidated:
            result["message"] = (
                f"Order {orderId} is already validated. Cannot add items."
            )
            return result
    except FileNotFoundError:
        result["message"] = f"Order with ID {orderId} not found."
        return result

    # Process each item
    for item_data in items:
        # Convert dict to AddItemRequest object if needed
        if isinstance(item_data, dict):
            item_request = AddItemRequest.model_validate(item_data)
        else:
            item_request = item_data

        # Get price from database
        price = get_price_from_db(item_request.itemId)
        if price is None:
            result["message"] = (
                f"Item with ID {item_request.itemId} not found in database."
            )
            continue

        existing_item = None

        # Check if item already exists in order (matching itemId AND indications)
        for order_item in order.items:
            if (
                order_item.itemId == item_request.itemId
                and order_item.indications == item_request.indications
            ):
                existing_item = order_item
                break

        if existing_item:
            # Update existing item quantity
            existing_item.quantity += item_request.quantity
            result["updated_count"] += 1
        else:
            # Add new item to order
            new_item = Item(
                itemId=item_request.itemId,
                quantity=item_request.quantity,
                price=price,
                indications=item_request.indications,
            )
            order.items.append(new_item)
            result["added_count"] += 1

    # Save the updated order
    try:
        with open(f"orders/{orderId}.json", "w") as f:
            json.dump(order.model_dump(), f, indent=2)
        result["success"] = True
        result["items"] = [item.model_dump() for item in order.items]
        result["message"] = (
            f"Successfully added {result['added_count']} new items and updated {result['updated_count']} existing items."
        )
    except Exception as e:
        result["message"] = f"Error saving order: {str(e)}"

    return result
