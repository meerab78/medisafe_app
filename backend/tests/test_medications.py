MEDICATIONS_URL = "/medications"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


def get_headers_for(client, email):
    # Register a user with this email, log in, and return the auth headers
    user_data = {
        "full_name": "Test User",
        "email": email,
        "password": "test12345",
        "timezone": "Asia/Karachi",
    }
    client.post(REGISTER_URL, json=user_data)

    login_data = {"email": email, "password": "test12345"}
    response = client.post(LOGIN_URL, json=login_data)
    token = response.json()["data"]["access_token"]
    return {"Authorization": "Bearer " + token}


def get_auth_headers(client):
    # First test user
    return get_headers_for(client, "test@example.com")


def get_other_user_headers(client):
    # Second test user (used for ownership tests)
    return get_headers_for(client, "other@example.com")


def make_medication_body(name="Paracetamol", medication_type="tablet"):
    # Returns a fresh dictionary each time, so tests do not affect each other
    body = {
        "name": name,
        "dosage": "500 mg",
        "medication_type": medication_type,
        "instructions": "Take after meal",
        "start_date": "2026-11-20",
        "end_date": "2026-12-20",
        "stock_quantity": 30,
        "low_stock_threshold": 5,
    }
    return body


def add_medication(client, headers, name="Paracetamol", medication_type="tablet"):
    body = make_medication_body(name, medication_type)
    return client.post(MEDICATIONS_URL, json=body, headers=headers)


# ---------------- Create ----------------


def test_create_medication_success(client):
    headers = get_auth_headers(client)
    response = add_medication(client, headers)
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["message"] == "Medication added successfully"
    assert body["data"]["name"] == "Paracetamol"
    assert body["data"]["is_active"] is True


def test_create_medication_invalid_type_fails(client):
    headers = get_auth_headers(client)
    response = add_medication(client, headers, medication_type="pill")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"
    assert body["errors"][0]["field"] == "medication_type"


def test_create_medication_end_date_before_start_date_fails(client):
    headers = get_auth_headers(client)
    data = make_medication_body()
    data["end_date"] = "2026-11-01"
    response = client.post(MEDICATIONS_URL, json=data, headers=headers)
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"


def test_create_medication_empty_name_fails(client):
    headers = get_auth_headers(client)
    data = make_medication_body()
    data["name"] = "   "
    response = client.post(MEDICATIONS_URL, json=data, headers=headers)

    assert response.status_code == 422


def test_create_medication_negative_stock_fails(client):
    headers = get_auth_headers(client)
    data = make_medication_body()
    data["stock_quantity"] = -5
    response = client.post(MEDICATIONS_URL, json=data, headers=headers)

    assert response.status_code == 422


def test_create_medication_without_token_fails(client):
    response = client.post(MEDICATIONS_URL, json=make_medication_body())

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)


# ---------------- List, search and filter ----------------


def test_list_medications_returns_active_sorted_by_name(client):
    headers = get_auth_headers(client)
    add_medication(client, headers, name="Paracetamol")
    add_medication(client, headers, name="Amoxicillin", medication_type="capsule")

    response = client.get(MEDICATIONS_URL, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert len(body["data"]) == 2
    assert body["data"][0]["name"] == "Amoxicillin"
    assert body["data"][1]["name"] == "Paracetamol"


def test_list_medications_search_by_name(client):
    headers = get_auth_headers(client)
    add_medication(client, headers, name="Paracetamol")
    add_medication(client, headers, name="Amoxicillin", medication_type="capsule")

    response = client.get(MEDICATIONS_URL, params={"search": "para"}, headers=headers)
    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Paracetamol"


def test_list_medications_filter_by_type(client):
    headers = get_auth_headers(client)
    add_medication(client, headers, name="Paracetamol", medication_type="tablet")
    add_medication(client, headers, name="Cough Syrup", medication_type="syrup")

    response = client.get(
        MEDICATIONS_URL, params={"medication_type": "syrup"}, headers=headers
    )
    body = response.json()

    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Cough Syrup"


# ---------------- Get one ----------------


def test_get_medication_success(client):
    headers = get_auth_headers(client)
    created = add_medication(client, headers)
    medication_id = created.json()["data"]["id"]

    response = client.get(MEDICATIONS_URL + "/" + str(medication_id), headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["id"] == medication_id
    assert body["data"]["name"] == "Paracetamol"


def test_get_medication_not_found(client):
    headers = get_auth_headers(client)
    response = client.get(MEDICATIONS_URL + "/9999", headers=headers)
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["message"] == "Medication not found"


# ---------------- Update ----------------


def test_update_medication_success(client):
    headers = get_auth_headers(client)
    created = add_medication(client, headers)
    medication_id = created.json()["data"]["id"]

    new_data = make_medication_body()
    new_data["dosage"] = "650 mg"
    new_data["is_active"] = True
    response = client.put(
        MEDICATIONS_URL + "/" + str(medication_id), json=new_data, headers=headers
    )
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Medication updated successfully"
    assert body["data"]["dosage"] == "650 mg"


def test_update_medication_not_found(client):
    headers = get_auth_headers(client)
    new_data = make_medication_body()
    new_data["is_active"] = True
    response = client.put(MEDICATIONS_URL + "/9999", json=new_data, headers=headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Medication not found"


# ---------------- Delete (soft delete) ----------------


def test_delete_medication_is_soft_delete(client):
    headers = get_auth_headers(client)
    created = add_medication(client, headers)
    medication_id = created.json()["data"]["id"]

    response = client.delete(MEDICATIONS_URL + "/" + str(medication_id), headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Medication deleted successfully"

    # It must disappear from the default (active) list
    active_list = client.get(MEDICATIONS_URL, headers=headers)
    assert len(active_list.json()["data"]) == 0

    # But the row must still exist as inactive
    inactive_list = client.get(
        MEDICATIONS_URL, params={"is_active": False}, headers=headers
    )
    inactive_data = inactive_list.json()["data"]
    assert len(inactive_data) == 1
    assert inactive_data[0]["is_active"] is False


def test_deleted_medication_can_be_restored(client):
    headers = get_auth_headers(client)
    created = add_medication(client, headers)
    medication_id = created.json()["data"]["id"]
    url = MEDICATIONS_URL + "/" + str(medication_id)

    client.delete(url, headers=headers)

    restore_data = make_medication_body()
    restore_data["is_active"] = True
    response = client.put(url, json=restore_data, headers=headers)

    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is True


# ---------------- Ownership (other user) ----------------


def test_other_user_cannot_get_my_medication(client):
    my_headers = get_auth_headers(client)
    created = add_medication(client, my_headers)
    medication_id = created.json()["data"]["id"]

    other_headers = get_other_user_headers(client)
    response = client.get(
        MEDICATIONS_URL + "/" + str(medication_id), headers=other_headers
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Medication not found"


def test_other_user_cannot_update_my_medication(client):
    my_headers = get_auth_headers(client)
    created = add_medication(client, my_headers)
    medication_id = created.json()["data"]["id"]

    other_headers = get_other_user_headers(client)
    new_data = make_medication_body()
    new_data["name"] = "Hacked"
    new_data["is_active"] = True
    response = client.put(
        MEDICATIONS_URL + "/" + str(medication_id),
        json=new_data,
        headers=other_headers,
    )

    assert response.status_code == 404

    # The original medication must stay unchanged
    check = client.get(MEDICATIONS_URL + "/" + str(medication_id), headers=my_headers)
    assert check.json()["data"]["name"] == "Paracetamol"


def test_other_user_cannot_delete_my_medication(client):
    my_headers = get_auth_headers(client)
    created = add_medication(client, my_headers)
    medication_id = created.json()["data"]["id"]

    other_headers = get_other_user_headers(client)
    response = client.delete(
        MEDICATIONS_URL + "/" + str(medication_id), headers=other_headers
    )

    assert response.status_code == 404

    # My medication must still be active
    check = client.get(MEDICATIONS_URL + "/" + str(medication_id), headers=my_headers)
    assert check.json()["data"]["is_active"] is True


def test_other_user_list_does_not_show_my_medications(client):
    my_headers = get_auth_headers(client)
    add_medication(client, my_headers)

    other_headers = get_other_user_headers(client)
    response = client.get(MEDICATIONS_URL, headers=other_headers)

    assert response.status_code == 200
    assert len(response.json()["data"]) == 0