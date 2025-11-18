import json
from pydantic import BaseModel
from models import Order, Item
from typing import Optional, List


class UpdateFormuleItemRequest(BaseModel):
    itemId: str
    quantity: Optional[int] = None
    indications: Optional[str] = None
    new_indications: Optional[str] = None
    action: str = "update"  # "update", "remove", or "replace"


async def update_formule_item(
    orderId: str,
    formuleIndex: int,
    updates: List[dict],
) -> dict:
    """
    Updates, removes, or replaces multiple items inside a formule in an existing order.
    Parameters:
    - orderId: str - The ID of the order
    - formuleIndex: int - Index of the formule to modify (0 = first formule, 1 = second, etc.)
    - updates: List[dict] - List of updates to apply, each containing:
        - itemId: str - The ID of the item to update
        - action: str - One of: "update" (change quantity), "remove" (delete item), "replace" (change indications)
        - quantity: Optional[int] - New quantity (for update action)
        - indications: Optional[str] - Current indications to match (to find the item)
        - new_indications: Optional[str] - New indications (for replace action, e.g., "sans champignon")

    Returns:
    - dict - Result with status, message, update counts, and updated formule
    """
    result = {
        "success": False,
        "total_updates": 0,
        "updates_by_action": {"update": 0, "remove": 0, "replace": 0},
        "message": "",
        "formule": {},
        "errors": [],
    }

    # Load the existing order
    try:
        with open(f"orders/{orderId}.json", "r") as f:
            order_data = json.load(f)
        order = Order.model_validate(order_data)
        if order.isValidated:
            result["message"] = (
                f"Order {orderId} is already validated. Cannot modify formules."
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

    formule = order.formules[formuleIndex]

    # Process each update
    for update_data in updates:
        if isinstance(update_data, dict):
            try:
                update_req = UpdateFormuleItemRequest.model_validate(update_data)
            except Exception as e:
                result["errors"].append(f"Invalid update format: {str(e)}")
                continue
        else:
            update_req = update_data

        # Find the item to update
        item_index = None
        for idx, item in enumerate(formule.items):
            if (
                item.itemId == update_req.itemId
                and item.indications == update_req.indications
            ):
                item_index = idx
                break

        if item_index is None:
            error_msg = f"Item {update_req.itemId} with indications '{update_req.indications}' not found in formule."
            result["errors"].append(error_msg)
            continue

        # Perform the action
        if update_req.action == "update":
            if update_req.quantity is None or update_req.quantity <= 0:
                result["errors"].append(
                    f"Item {update_req.itemId}: quantity must be positive."
                )
                continue
            formule.items[item_index].quantity = update_req.quantity
            result["updates_by_action"]["update"] += 1
            result["total_updates"] += 1

        elif update_req.action == "remove":
            formule.items.pop(item_index)
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
            for item in formule.items:
                if (
                    item.itemId == update_req.itemId
                    and item.indications == update_req.new_indications
                ):
                    existing_variant = item
                    break

            if existing_variant:
                # Merge quantities if variant already exists
                existing_variant.quantity += formule.items[item_index].quantity
                formule.items.pop(item_index)
            else:
                # Just update the indications
                formule.items[item_index].indications = update_req.new_indications

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
        result["formule"] = {
            "formuleId": formule.formuleId,
            "formuleName": formule.formuleName,
            "items": [item.model_dump() for item in formule.items],
        }

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
