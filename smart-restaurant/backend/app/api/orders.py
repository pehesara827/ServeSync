"""Order API endpoints backed by Supabase."""
import httpx
from fastapi import APIRouter, HTTPException

from ..models.order import OrderCreate, StatusUpdate
from ..services import order_service
from .errors import supabase_http_exception, supabase_network_exception

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _supabase_error(exc: httpx.HTTPError) -> HTTPException:
    """Maps Supabase transport errors; preserves real status codes."""
    if isinstance(exc, httpx.HTTPStatusError):
        return supabase_http_exception(exc)
    return supabase_network_exception(exc)


@router.get("")
def list_orders(status: str | None = None):
    """Lists orders with items in arrival order (oldest first, newest last)."""
    try:
        return order_service.fetch_orders(status)
    except httpx.HTTPStatusError as exc:
        raise supabase_http_exception(exc) from exc
    except httpx.HTTPError as exc:
        raise supabase_network_exception(exc) from exc


@router.get("/{order_id}")
def get_order(order_id: int):
    try:
        return order_service.fetch_one(order_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise supabase_http_exception(exc) from exc
    except httpx.HTTPError as exc:
        raise supabase_network_exception(exc) from exc


@router.post("", status_code=201)
def create_order(payload: OrderCreate):
    try:
        return order_service.create_order(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise supabase_http_exception(exc) from exc
    except httpx.HTTPError as exc:
        raise supabase_network_exception(exc) from exc


@router.patch("/{order_id}")
def change_status(order_id: int, payload: StatusUpdate):
    try:
        return order_service.update_status(order_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise supabase_http_exception(exc) from exc
    except httpx.HTTPError as exc:
        raise supabase_network_exception(exc) from exc
