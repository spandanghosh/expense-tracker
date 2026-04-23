# Expense Tracker

A production-grade full-stack expense tracker built as a take-home assignment. FastAPI backend with SQLite stores monetary values in paise to avoid floating-point errors; React + Vite + TypeScript frontend handles idempotent form submissions and client-side filtering/totaling.

## Live URLs

| Service  | URL |
|----------|-----|
| Frontend | https://expense-tracker-six-sepia-13.vercel.app |
| Backend  | https://expense-tracker-le2w.onrender.com |

---

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # adjust values if needed
alembic upgrade head             # create tables
uvicorn app.main:app --reload    # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local       # set VITE_API_BASE_URL=http://localhost:8000
npm run dev                      # http://localhost:5173
```

---

## API Contract

### `GET /healthz`
```
200 OK  →  {"status": "ok"}
```

### `POST /expenses`
**Required header:** `Idempotency-Key: <uuid4>`

**Request body:**
```json
{
  "amount": "150.75",
  "category": "Food",
  "description": "Lunch at office",
  "date": "2026-04-23"
}
```

**Responses:**
| Status | Meaning |
|--------|---------|
| `201`  | Created — returns the saved expense |
| `400`  | Missing `Idempotency-Key` header |
| `422`  | Validation failure (amount ≤ 0, bad date, empty category, etc.) |

**Error shape (RFC 7807 `application/problem+json`):**
```json
{
  "type": "https://httpstatuses.com/422",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "amount must be greater than 0"
}
```

### `GET /expenses`
**Query params:** `category` (optional), `sort` (`date_asc` | `date_desc`, default `date_desc`)

**Response:**
```json
[
  {
    "id": 1,
    "amount": "150.75",
    "category": "Food",
    "description": "Lunch at office",
    "date": "2026-04-23",
    "created_at": "2026-04-23T10:00:00"
  }
]
```

---

## Design Decisions

### Persistence — SQLite
Chosen for zero-config local dev. The Alembic migration runs on startup; switching to Postgres on Render requires only changing `DATABASE_URL`.

### Idempotency mechanism
- Client generates a UUID v4 per form submission (reused across retries).
- Server stores `(key, response_body, status_code)` in `idempotency_keys` table for 24 h.
- Duplicate `POST` within 24 h replays the stored response — no second row in `expenses`.
- Missing header → immediate `400`. Silent non-idempotent writes are not allowed.

### Money handling
All monetary values stored as `amount_minor INTEGER` (paise = rupees × 100). The API boundary uses Pydantic `Decimal` with 2 decimal places. Floating-point arithmetic for currency is never used.

---

## Trade-offs Made for Timebox

- **SQLite over Postgres** — SQLite is zero-config and sufficient for a demo. A persistent disk must be mounted on Render (or swapped for Postgres) for data durability.
- **No auth layer** — JWT/OAuth2 is omitted; this is a local/demo deployment only.
- **Optimistic prepend then server-reconcile** — on form submit, the new expense is prepended locally and a fresh `GET` is triggered. In a high-traffic app a cursor-based approach would be cleaner.
- **Single file for all components** — all React components are in `App.tsx` (≈ 300 lines). Would split into separate files in a larger codebase.

---

## Intentional Omissions (with more time)

1. **Edit / Delete** — `PATCH /expenses/{id}` and `DELETE /expenses/{id}`
2. **Pagination** — `limit` / `offset` or cursor on `GET /expenses`
3. **Full-text search** — fuzzy category / description search
4. **Rate limiting** — `slowapi` middleware for production
5. **CSV export** — accounting convenience feature
6. **Postgres** — swap `DATABASE_URL` and run `alembic upgrade head`
7. **User authentication** — FastAPI `Depends` with JWT; one user per token

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Expected: **17 passed**.

---

## Seeding Sample Data

Render's SQLite database is wiped on every redeploy. To restore sample expenses after a redeploy, run from the repo root:

```bash
python seed.py
```

This posts 12 realistic expenses via the live API. Run it once manually — it is intentionally not wired into the deploy pipeline to avoid duplicate rows.

Expected: **17 passed** covering idempotency, filter/sort correctness, and all validation rules.
