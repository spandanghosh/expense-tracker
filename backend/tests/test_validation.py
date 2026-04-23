import uuid


def test_amount_zero_rejected(client):
    resp = client.post("/expenses", json={"amount": "0", "category": "Food", "date": "2026-04-23"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_amount_negative_rejected(client):
    resp = client.post("/expenses", json={"amount": "-10.00", "category": "Food", "date": "2026-04-23"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_date_missing_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "Food"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_date_malformed_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "Food", "date": "not-a-date"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_date_too_far_future_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "Food", "date": "2030-01-01"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_category_empty_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "", "date": "2026-04-23"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_category_too_long_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "X" * 51, "date": "2026-04-23"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_description_too_long_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "Food", "date": "2026-04-23", "description": "X" * 501}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422


def test_unknown_field_rejected(client):
    resp = client.post("/expenses", json={"amount": "10.00", "category": "Food", "date": "2026-04-23", "extra_field": "oops"}, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert resp.status_code == 422
