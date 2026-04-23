import uuid


def post_expense(client, amount, category, date):
    return client.post(
        "/expenses",
        json={"amount": amount, "category": category, "date": date, "description": ""},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )


def test_category_filter(client):
    post_expense(client, "10.00", "Food", "2026-04-20")
    post_expense(client, "20.00", "Transport", "2026-04-21")
    post_expense(client, "30.00", "Food", "2026-04-22")

    resp = client.get("/expenses?category=Food")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert all(e["category"] == "Food" for e in items)


def test_date_desc_sort(client):
    post_expense(client, "10.00", "Food", "2026-04-20")
    post_expense(client, "20.00", "Food", "2026-04-22")
    post_expense(client, "30.00", "Food", "2026-04-21")

    resp = client.get("/expenses?sort=date_desc")
    dates = [e["date"] for e in resp.json()]
    assert dates == sorted(dates, reverse=True)


def test_date_asc_sort(client):
    post_expense(client, "10.00", "Food", "2026-04-22")
    post_expense(client, "20.00", "Food", "2026-04-20")
    post_expense(client, "30.00", "Food", "2026-04-21")

    resp = client.get("/expenses?sort=date_asc")
    dates = [e["date"] for e in resp.json()]
    assert dates == sorted(dates)


def test_category_filter_and_sort_combined(client):
    post_expense(client, "10.00", "Food", "2026-04-20")
    post_expense(client, "20.00", "Transport", "2026-04-22")
    post_expense(client, "30.00", "Food", "2026-04-22")

    resp = client.get("/expenses?category=Food&sort=date_asc")
    items = resp.json()
    assert len(items) == 2
    assert items[0]["date"] <= items[1]["date"]
