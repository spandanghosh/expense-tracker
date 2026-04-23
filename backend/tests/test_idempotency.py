import uuid


VALID_PAYLOAD = {
    "amount": "100.50",
    "category": "Food",
    "description": "Lunch",
    "date": "2026-04-23",
}


def test_missing_idempotency_key_returns_400(client):
    resp = client.post("/expenses", json=VALID_PAYLOAD)
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == 400
    assert "Idempotency-Key" in body["detail"]


def test_same_key_twice_creates_only_one_row(client):
    key = str(uuid.uuid4())
    headers = {"Idempotency-Key": key}

    resp1 = client.post("/expenses", json=VALID_PAYLOAD, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/expenses", json=VALID_PAYLOAD, headers=headers)
    assert resp2.status_code == 201

    assert resp1.json()["id"] == resp2.json()["id"]

    all_expenses = client.get("/expenses").json()
    assert len(all_expenses) == 1


def test_different_keys_create_separate_rows(client):
    resp1 = client.post("/expenses", json=VALID_PAYLOAD, headers={"Idempotency-Key": str(uuid.uuid4())})
    resp2 = client.post("/expenses", json=VALID_PAYLOAD, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] != resp2.json()["id"]
    assert len(client.get("/expenses").json()) == 2


def test_replay_returns_identical_response(client):
    key = str(uuid.uuid4())
    headers = {"Idempotency-Key": key}
    resp1 = client.post("/expenses", json=VALID_PAYLOAD, headers=headers)
    resp2 = client.post("/expenses", json=VALID_PAYLOAD, headers=headers)
    assert resp1.json() == resp2.json()
