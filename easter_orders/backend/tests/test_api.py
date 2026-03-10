from app import create_app, db


def client():
    app = create_app("sqlite:///:memory:")
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    return app.test_client()


def create_customer(test_client):
    response = test_client.post(
        "/api/customers",
        json={"name": "Maria", "phone": "11999998888", "email": "maria@x.com"},
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def test_requires_50_percent_down_payment():
    test_client = client()
    customer_id = create_customer(test_client)
    payload = {
        "customer_id": customer_id,
        "total_value": 100,
        "down_payment": 40,
        "items": [{"quantity": 1, "size": "250g", "shell": "ao leite", "filling": "brigadeiro", "unit_price": 100}],
    }
    response = test_client.post("/api/orders", json=payload)
    assert response.status_code == 400


def test_report_totals_by_size():
    test_client = client()
    customer_id = create_customer(test_client)
    payload = {
        "customer_id": customer_id,
        "total_value": 200,
        "down_payment": 100,
        "items": [
            {"quantity": 2, "size": "250g", "shell": "ao leite", "filling": "brigadeiro", "unit_price": 50},
            {"quantity": 1, "size": "500g", "shell": "branca", "filling": "ninho", "unit_price": 100},
        ],
    }
    create_response = test_client.post("/api/orders", json={**payload, "delivery_forecast": "2026-03-30"})
    assert create_response.status_code == 201
    created_order = create_response.get_json()
    assert created_order["delivery_forecast"] == "2026-03-30"
    assert created_order["order_date"]

    report = test_client.get("/api/reports/totals")
    data = report.get_json()
    assert report.status_code == 200
    sizes = {row["size"]: row["quantity"] for row in data["eggs_by_size"]}
    assert sizes["250g"] == 2
    assert sizes["500g"] == 1
