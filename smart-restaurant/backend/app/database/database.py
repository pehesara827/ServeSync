"""Supabase REST connection helpers shared by the API routers."""
import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("supabase")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kpcvtffhdvdpapoepksa.supabase.co").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

if not SUPABASE_ANON_KEY:
    logger.warning("SUPABASE_ANON_KEY is empty - all Supabase calls will 401. Check backend/.env.")


def supabase_headers() -> dict:
    """Headers every Supabase REST request needs."""
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _url(path: str) -> str:
    """Builds a PostgREST URL; path must not contain a query string."""
    clean = path.lstrip("/").split("?")[0]
    return f"{SUPABASE_URL}/rest/v1/{clean}"


def sb_get(path: str, params: dict | None = None) -> httpx.Response:
    """GET helper for Supabase REST paths like 'orders'."""
    return httpx.get(_url(path), headers=supabase_headers(), params=params, timeout=15)


def sb_post(path: str, payload: dict | list, params: dict | None = None) -> httpx.Response:
    """POST helper used to create orders and order items."""
    return httpx.post(_url(path), headers=supabase_headers(), json=payload, params=params, timeout=15)


def sb_patch(path: str, payload: dict, params: dict | None = None) -> httpx.Response:
    """PATCH helper used to update an order status. Pass filters via params."""
    return httpx.patch(_url(path), headers=supabase_headers(), json=payload, params=params, timeout=15)
