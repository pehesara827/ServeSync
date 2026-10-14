"""Maps Supabase/PostgREST failures to honest FastAPI errors with logging."""
import logging

import httpx
from fastapi import HTTPException

logger = logging.getLogger("supabase")


def supabase_http_exception(exc: httpx.HTTPStatusError) -> HTTPException:
    """Forward Supabase status/body instead of a blanket 502."""
    try:
        body = (exc.response.text or "")[:2000]
    except Exception:  # pragma: no cover - defensive
        body = ""
    status = exc.response.status_code if exc.response is not None else 502
    logger.error("Supabase %s for %s: %s", status, exc.request.url if exc.request else "?", body)

    # Missing tables is a backend/schema misconfiguration, not a bad gateway.
    if "PGRST205" in body or "schema cache" in body:
        return HTTPException(
            status_code=500,
            detail=(
                "Supabase tables 'public.orders' / 'public.order_items' not found "
                "(PGRST205 schema cache). Create them in Supabase SQL Editor, then retry. "
                f"Supabase said: {body}"
            ),
        )
    if status in (401, 403):
        return HTTPException(
            status_code=500,
            detail=f"Supabase auth failed ({status}): check SUPABASE_ANON_KEY. Body: {body}",
        )
    if 400 <= status < 500:
        return HTTPException(status_code=status, detail=f"Supabase error ({status}): {body or exc}")
    return HTTPException(status_code=502, detail=f"Supabase error: {body or exc}")


def supabase_network_exception(exc: httpx.HTTPError) -> HTTPException:
    """Timeouts / DNS / connection drops stay a 502."""
    logger.error("Supabase network error for %s: %s", getattr(exc.request, "url", "?"), exc)
    return HTTPException(status_code=502, detail=f"Supabase unreachable: {exc}")
