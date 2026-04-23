# Design Decisions & API Contract

## SQL DDL

```sql
CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),  -- paise (rupees × 100)
    category    TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    date        TEXT    NOT NULL,  -- ISO 8601 YYYY-MM-DD
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE idempotency_keys (
    key          TEXT    PRIMARY KEY,
    response_body TEXT   NOT NULL,
    status_code  INTEGER NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

**Money handling**: All monetary values stored as integers in paise (rupees × 100) to avoid floating-point errors. The API boundary uses `Decimal` with 2 decimal places via Pydantic. Conversion: `amount_minor = int(amount * 100)`.

## API Contract

### `GET /healthz`
- **Response 200**: `{"status": "ok"}`

### `POST /expenses`
- **Headers**: `Idempotency-Key: <uuid4>` (required)
- **Request body** (`application/json`):
  ```json
  {
    "amount": "150.75",
    "category": "Food",
    "description": "Lunch at office",
    "date": "2026-04-23"
  }
  ```
- **Response 201** (`application/json`):
  ```json
  {
    "id": 1,
    "amount": "150.75",
    "category": "Food",
    "description": "Lunch at office",
    "date": "2026-04-23",
    "created_at": "2026-04-23T10:00:00"
  }
  ```
- **Response 400** — missing `Idempotency-Key` header:
  ```json
  {
    "type": "https://httpstatuses.com/400",
    "title": "Bad Request",
    "status": 400,
    "detail": "Idempotency-Key header is required"
  }
  ```
- **Response 422** — validation failure (RFC 7807):
  ```json
  {
    "type": "https://httpstatuses.com/422",
    "title": "Unprocessable Entity",
    "status": 422,
    "detail": "amount must be greater than 0"
  }
  ```

### `GET /expenses`
- **Query params**:
  - `category` (optional): filter by exact category name
  - `sort` (optional): `date_asc` | `date_desc` (default: `date_desc`)
- **Response 200** (`application/json`):
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

## Idempotency Flow

1. Client generates a UUID v4 `Idempotency-Key` per form submission (reused on retries).
2. Server receives `POST /expenses`:
   a. If header missing → 400 immediately.
   b. Look up `key` in `idempotency_keys` table.
   c. If found **and** `created_at` < 24h ago → return stored `response_body` + `status_code` verbatim (no DB write to `expenses`).
   d. If not found → process normally, write to `expenses`, then store the serialized response + status code in `idempotency_keys`.
3. Client on network failure: retries the same request with the same key. Server replays the cached response, client gets same result.

## Validation Rules

| Field | Rule | Status |
|-------|------|--------|
| `amount` | must be Decimal > 0, 2 decimal places | 422 |
| `date` | ISO 8601, not more than 1 day in future | 422 |
| `category` | non-empty, ≤ 50 chars | 422 |
| `description` | ≤ 500 chars | 422 |
| Unknown fields | rejected (`extra="forbid"`) | 422 |

## Deferred Items (Ranked)

1. **Authentication** — no user auth layer; demo/local only. Would add JWT with FastAPI's `Depends` if deployed publicly.
2. **Pagination** — `GET /expenses` returns all rows; a real app would add `limit`/`offset` or cursor pagination.
3. **Edit / Delete endpoints** — `PATCH /expenses/{id}` and `DELETE /expenses/{id}` are not implemented; read-only after creation.
4. **Full-text search** — category filter is exact match; fuzzy search would require a search index.
5. **CSV export** — useful for accounting but out of scope.
6. **Rate limiting** — no request throttling; would add slowapi middleware for production.
7. **PostgreSQL** — SQLite chosen for zero-config local dev; Render supports Postgres with minimal migration changes.
