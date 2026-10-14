# Smart Restaurant

Starter scaffold for a React/Vite frontend, Python/FastAPI backend, and ESP32 robot.

## Run locally

Frontend: run `npm install` and `npm run dev` from `frontend/`.

Backend: install `backend/requirements.txt`, then run `uvicorn app.main:app --reload` from `backend/`.

## Supabase setup

The backend reads and writes orders in the Supabase `public` schema. In the
Supabase project configured by `backend/.env`, open **SQL Editor**, run the
contents of [`backend/supabase/schema.sql`](backend/supabase/schema.sql), and
then restart or retry the backend request. This creates `orders` and
`order_items`, their foreign-key relationship, and the access policies used by
the current unauthenticated API.

The architecture and circuit diagrams are not included yet; add the real diagrams under `docs/` when available.