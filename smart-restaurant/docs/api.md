# API

The FastAPI application starts at `backend/app/main.py`.

- `GET /health` confirms that the backend is responding.
- `GET /api/orders?status=pending|completed|cancelled` lists orders with their items. Orders come back in **arrival order**: the first order placed is first and the freshest order is last, so a new order shows up at the bottom of the kitchen board.
- `GET /api/kitchen/orders?status=...` is the kitchen board feed, with the same arrival ordering.
- `GET /api/orders/{order_id}` returns one order with its items.
- `POST /api/orders` creates an order (`table_number`, `status`, `items`).
- `PATCH /api/orders/{order_id}` updates a status (`pending`, `completed`, `cancelled`).
