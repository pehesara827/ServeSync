"""Order business logic proxied to Supabase REST."""
import logging

from ..database.database import sb_get, sb_patch, sb_post
from ..iot.mqtt_client import publish_robot_command
from ..models.order import OrderCreate

logger = logging.getLogger("orders")


VALID_STATUSES = {"pending", "completed", "cancelled"}


def normalize_status(value: str) -> str:
    text = str(value or "").lower().strip()
    if text in ("complited", "complete", "done"):
        return "completed"
    if text in ("cancel", "canceled"):
        return "cancelled"
    return text


def row_to_order(row: dict) -> dict:
    items = [
        {
            "id": item.get("id"),
            "item_name": item.get("item_name"),
            "price": item.get("price", 0),
            "quantity": item.get("quantity", 0),
        }
        for item in (row.get("order_items") or [])
    ]
    total = sum(item["price"] * item["quantity"] for item in items)
    return {
        "id": row.get("id"),
        "table_number": row.get("table_number"),
        "status": normalize_status(row.get("status", "pending")),
        "created_at": row.get("created_at"),
        "items": items,
        "total": total,
    }


def fetch_orders(status: str | None = None) -> list[dict]:
    """Returns orders in arrival order: first order placed first, newest last."""
    params = {"select": "*,order_items(*)", "order": "created_at.asc,id.asc"}
    if status and status != "all":
        params["status"] = f"eq.{normalize_status(status)}"
    response = sb_get("orders", params=params)
    response.raise_for_status()
    return [row_to_order(row) for row in response.json()]


def update_status(order_id: int, status: str) -> dict:
    cleaned = normalize_status(status)
    if cleaned not in VALID_STATUSES:
        raise ValueError("Status must be pending, completed or cancelled")
    response = sb_patch("orders", {"status": cleaned}, params={"id": f"eq.{order_id}"})
    response.raise_for_status()
    rows = response.json()
    if not rows:
        raise LookupError(f"Order {order_id} not found")
    # Re-fetch with items so dashboard gets the full card.
    full = sb_get("orders", params={"select": "*,order_items(*)", "id": f"eq.{order_id}"})
    full.raise_for_status()
    full_rows = full.json()
    order = row_to_order(full_rows[0]) if full_rows else row_to_order(rows[0])
    # Instant robot dispatch: a COMPLETED kitchen order means "deliver now".
    # Fail-open on purpose - broker downtime must never break the order update.
    # The envelope below lets the frontend toast "saved but robot offline".
    robot_dispatch = {"attempted": False, "delivered": False}
    if cleaned == "completed":
        robot_dispatch["attempted"] = True
        try:
            delivered = publish_robot_command(
                table_number=order.get("table_number"),
                order_id=order.get("id", order_id),
            )
            robot_dispatch["delivered"] = bool(delivered)
            if not delivered:
                logger.warning("Robot dispatch failed for order %s (saved as completed)", order_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Robot MQTT notify failed for order %s: %s", order_id, exc)
    order["robot_dispatch"] = robot_dispatch
    return order


def create_order(payload: OrderCreate) -> dict:
    status = normalize_status(payload.status)
    if status not in VALID_STATUSES:
        raise ValueError("Status must be pending, completed or cancelled")
    created = sb_post("orders", {"table_number": payload.table_number, "status": status})
    created.raise_for_status()
    order_row = created.json()[0]
    if payload.items:
        items_payload = [
            {"order_id": order_row["id"], "item_name": i.item_name, "price": i.price, "quantity": i.quantity}
            for i in payload.items
        ]
        items_res = sb_post("order_items", items_payload)
        items_res.raise_for_status()
    return fetch_one(order_row["id"])


def fetch_one(order_id: int) -> dict:
    response = sb_get("orders", params={"select": "*,order_items(*)", "id": f"eq.{order_id}"})
    response.raise_for_status()
    rows = response.json()
    if not rows:
        raise LookupError(f"Order {order_id} not found")
    return row_to_order(rows[0])
