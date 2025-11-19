import json
from pydantic import BaseModel
from ...models import Order, Item
from typing import Optional, List


class UpdateItemRequest(BaseModel):
    itemId: str
    quantity: Optional[int] = None
    indications: Optional[str] = None
    new_indications: Optional[str] = None
    action: str = "update"  # "update", "remove", or "replace"


async def update_item_order(
    orderId: str,
    updates: List[dict],
) -> dict:
    """
    Updates, removes, or replaces multiple items in an existing order in a single operation.
    Parameters:
    - orderId: str - The ID of the order
    - updates: List[dict] - List of updates to apply, each containing:
        - itemId: str - The ID of the item to update
        - action: str - One of: "update" (change quantity), "remove" (delete item), "replace" (change indications)
        - quantity: Optional[int] - New quantity (for update action)
        - indications: Optional[str] - Current indications to match (to find the item)
        - new_indications: Optional[str] - New indications (for replace action, e.g., "sans champignon")

    Returns:
    - dict - Result with status, message, update counts, and updated order

    Examples:
    - Update quantity: {"itemId": "plat_001", "quantity": 3, "indications": None, "action": "update"}
    - Remove item: {"itemId": "plat_001", "indications": None, "action": "remove"}
    - Replace indications: {"itemId": "plat_001", "indications": None, "new_indications": "sans champignon", "action": "replace"}
    """
    result = {
        "success": False,
        "total_updates": 0,
        "updates_by_action": {"update": 0, "remove": 0, "replace": 0},
        "message": "",
        "items": [],
        "errors": [],
    }

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
        order = Order.model_validate(order_data)
        if order.isValidated:
            result["message"] = (
                f"Order {orderId} is already validated. Cannot modify items."
            )
            return result
    except FileNotFoundError:
        result["message"] = f"Order with ID {orderId} not found."
        return result

    # Process each update
    for update_data in updates:
        # Convert dict to UpdateItemRequest object if needed
        if isinstance(update_data, dict):
            try:
                update_req = UpdateItemRequest.model_validate(update_data)
            except Exception as e:
                result["errors"].append(f"Invalid update format: {str(e)}")
                continue
        else:
            update_req = update_data

        # Find the item to update
        item_index = None
        for idx, order_item in enumerate(order.items):
            if (
                order_item.itemId == update_req.itemId
                and order_item.indications == update_req.indications
            ):
                item_index = idx
                break

        if item_index is None:
            error_msg = f"Item {update_req.itemId} with indications '{update_req.indications}' not found."
            result["errors"].append(error_msg)
            continue

        # Perform the action
        if update_req.action == "update":
            if update_req.quantity is None or update_req.quantity <= 0:
                result["errors"].append(
                    f"Item {update_req.itemId}: quantity must be positive."
                )
                continue
            order.items[item_index].quantity = update_req.quantity
            result["updates_by_action"]["update"] += 1
            result["total_updates"] += 1

        elif update_req.action == "remove":
            removed_item = order.items.pop(item_index)
            result["updates_by_action"]["remove"] += 1
            result["total_updates"] += 1

        elif update_req.action == "replace":
            if update_req.new_indications is None:
                result["errors"].append(
                    f"Item {update_req.itemId}: new indications must be provided for replace action."
                )
                continue

            # Check if an item with same itemId but new indications already exists
            existing_variant = None
            for order_item in order.items:
                if (
                    order_item.itemId == update_req.itemId
                    and order_item.indications == update_req.new_indications
                ):
                    existing_variant = order_item
                    break

            if existing_variant:
                # Merge quantities if variant already exists
                existing_variant.quantity += order.items[item_index].quantity
                order.items.pop(item_index)
            else:
                # Just update the indications
                order.items[item_index].indications = update_req.new_indications

            result["updates_by_action"]["replace"] += 1
            result["total_updates"] += 1

        else:
            result["errors"].append(
                f"Item {update_req.itemId}: unknown action '{update_req.action}'."
            )

    # Save the updated order
    try:
        with open(f"orders/{orderId}.json", "w") as f:
            json.dump(order.model_dump(), f, indent=2)
        result["success"] = True
        result["items"] = [item.model_dump() for item in order.items]

        # Build summary message
        if result["total_updates"] > 0:
            msg_parts = []
            if result["updates_by_action"]["update"] > 0:
                msg_parts.append(f"{result['updates_by_action']['update']} update(s)")
            if result["updates_by_action"]["remove"] > 0:
                msg_parts.append(f"{result['updates_by_action']['remove']} removal(s)")
            if result["updates_by_action"]["replace"] > 0:
                msg_parts.append(
                    f"{result['updates_by_action']['replace']} replacement(s)"
                )
            result["message"] = f"Successfully applied {', '.join(msg_parts)}."

        if result["errors"]:
            result["message"] += f" Errors: {'; '.join(result['errors'])}"

    except Exception as e:
        result["message"] = f"Error saving order: {str(e)}"

    return result
