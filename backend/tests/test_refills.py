from datetime import date

from app.database.connection import get_db
from app.models.medication_model import Medication


def get_test_db(client):
    override_function = client.app.dependency_overrides[get_db]
    db_generator = override_function()
    return next(db_generator)


def register_and_login(client, email="refill@example.com"):
    user_data = {
        "full_name": "Refill User",
        "email": email,
        "password": "test12345",
        "timezone": "UTC",
    }
    client.post("/auth/register", json=user_data)
    login_data = {"email": email, "password": "test12345"}
    login_response = client.post("/auth/login", json=login_data)
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    profile_response = client.get("/users/me", headers=headers)
    user_id = profile_response.json()["data"]["id"]
    return headers, user_id


def add_medication(db, user_id, name="Metformin", stock=10, threshold=5, is_active=True):
    medication = Medication(
        user_id=user_id,
        name=name,
        dosage="500 mg",
        medication_type="tablet",
        start_date=date(2026, 1, 1),
        stock_quantity=stock,
        low_stock_threshold=threshold,
        is_active=is_active,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)
    medication_id = medication.id
    return medication_id


def refill_url(medication_id):
    return "/medications/" + str(medication_id) + "/refill"


def stock_url(medication_id):
    return "/medications/" + str(medication_id) + "/stock"


def history_url(medication_id):
    return "/medications/" + str(medication_id) + "/refills"


def test_refill_adds_stock(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id = add_medication(db, user_id, stock=10)
    db.close()

    response = client.post(
        refill_url(medication_id), json={"quantity_added": 20}, headers=headers
    )
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["data"]["quantity_added"] == 20
    assert body["data"]["stock_quantity"] == 30
    assert body["data"]["is_low_stock"] is False


def test_refill_with_zero_quantity_fails(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id = add_medication(db, user_id)
    db.close()

    response = client.post(
        refill_url(medication_id), json={"quantity_added": 0}, headers=headers
    )
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"


def test_refill_other_users_medication_returns_404(client):
    headers_one, user_one_id = register_and_login(client, "one@example.com")
    headers_two, user_two_id = register_and_login(client, "two@example.com")
    db = get_test_db(client)
    medication_id = add_medication(db, user_one_id)
    db.close()

    response = client.post(
        refill_url(medication_id), json={"quantity_added": 5}, headers=headers_two
    )
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["message"] == "Medication not found"


def test_refill_inactive_medication_fails(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id = add_medication(db, user_id, is_active=False)
    db.close()

    response = client.post(
        refill_url(medication_id), json={"quantity_added": 5}, headers=headers
    )
    body = response.json()

    assert response.status_code == 400
    assert body["message"] == "This medication is not active"


def test_set_stock_updates_and_flags_low_stock(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id = add_medication(db, user_id, stock=10, threshold=5)
    db.close()

    response = client.put(
        stock_url(medication_id), json={"stock_quantity": 3}, headers=headers
    )
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["stock_quantity"] == 3
    assert body["data"]["is_low_stock"] is True


def test_set_stock_negative_fails(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id = add_medication(db, user_id)
    db.close()

    response = client.put(
        stock_url(medication_id), json={"stock_quantity": -1}, headers=headers
    )

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_refill_history_is_newest_first(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id = add_medication(db, user_id)
    db.close()

    client.post(refill_url(medication_id), json={"quantity_added": 5}, headers=headers)
    client.post(refill_url(medication_id), json={"quantity_added": 7}, headers=headers)

    response = client.get(history_url(medication_id), headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["total"] == 2
    assert body["data"]["refills"][0]["quantity_added"] == 7
    assert body["data"]["refills"][1]["quantity_added"] == 5


def test_low_stock_list(client):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    add_medication(db, user_id, name="Low One", stock=3, threshold=5)
    add_medication(db, user_id, name="Equal One", stock=5, threshold=5)
    add_medication(db, user_id, name="Enough", stock=10, threshold=5)
    add_medication(db, user_id, name="Deleted", stock=0, threshold=5, is_active=False)
    db.close()

    response = client.get("/refills/low-stock", headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["total"] == 2
    assert body["data"]["medications"][0]["medication_name"] == "Low One"
    assert body["data"]["medications"][1]["medication_name"] == "Equal One"


def test_refill_endpoints_require_token(client):
    low_stock_response = client.get("/refills/low-stock")
    refill_response = client.post(refill_url(1), json={"quantity_added": 5})

    assert low_stock_response.status_code in (401, 403)
    assert refill_response.status_code in (401, 403)