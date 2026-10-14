"""Kitchen workflow API endpoints backed by Supabase."""
import httpx
from fastapi import APIRouter

from ..services import order_service
from .errors import supabase_http_exception, supabase_network_exception

router = APIRouter(prefix="/api/kitchen", tags=["kitchen"])


@router.get("/orders")
def kitchen_orders(status: str | None = None):
    """Kitchen board feed in arrival order; optional ?status=pending|completed|cancelled."""
    try:
        return order_service.fetch_orders(status)
    except httpx.HTTPStatusError as exc:
        raise supabase_http_exception(exc) from exc
    except httpx.HTTPError as exc:
        raise supabase_network_exception(exc) from exc
