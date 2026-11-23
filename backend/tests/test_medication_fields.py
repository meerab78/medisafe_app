MEDICATIONS_URL = "/medications"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


def get_auth_headers(client):
    user_data = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "test12345",
        "timezone": "Asia/Karachi",
    }
    client.post(REGISTER_URL, json=user_data)
    login_data = {"email": "test@example.com", "password": "test12345"}
    response = client.post(LOGIN_URL, json=login_data)
    token = response.json()["data"]["access_token"]
    return {"Authorization": "Bearer " + token}


def make_body():
    # Returns a fresh dictionary each time
    body = {
        "name": "Paracetamol",
        "dosage": "500 mg",
        "medication_type": "pill",
        "start_date": "2026-11-21",
    }
    return body


def test_create_with_all_new_fields(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["medication_type"] = "other"
    body["route"] = "ears"
    body["reason"] = "Ear infection"
    body["icon"] = "drops"
    body["food_instruction"] = "after_meal"

    response = client.post(MEDICATIONS_URL, json=body, headers=headers)
    data = response.json()["data"]

    assert response.status_code == 201
    assert data["route"] == "ears"
    assert data["reason"] == "Ear infection"
    assert data["icon"] == "drops"
    assert data["food_instruction"] == "after_meal"

    # The same values must come back when we read it again
    medication_id = data["id"]
    check = client.get(MEDICATIONS_URL + "/" + str(medication_id), headers=headers)
    assert check.json()["data"]["route"] == "ears"
    assert check.json()["data"]["food_instruction"] == "after_meal"


def test_new_fields_have_defaults(client):
    headers = get_auth_headers(client)
    response = client.post(MEDICATIONS_URL, json=make_body(), headers=headers)
    data = response.json()["data"]

    assert response.status_code == 201
    assert data["route"] is None
    assert data["reason"] is None
    assert data["icon"] is None
    assert data["food_instruction"] == "any"


def test_invalid_food_instruction_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["food_instruction"] = "morning"
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)
    result = response.json()

    assert response.status_code == 422
    assert result["success"] is False
    assert result["message"] == "Invalid input data"
    assert result["errors"][0]["field"] == "food_instruction"


def test_invalid_route_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["medication_type"] = "other"
    body["route"] = "eyes"
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "route"


def test_other_form_without_route_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["medication_type"] = "other"
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["message"] == "Invalid input data"


def test_route_is_cleared_when_form_is_not_other(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["route"] = "mouth"
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)

    assert response.status_code == 201
    assert response.json()["data"]["route"] is None


def test_invalid_icon_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["icon"] = "rocket"
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "icon"


def test_old_form_name_is_rejected(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["medication_type"] = "tablet"
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "medication_type"


def test_update_changes_new_fields(client):
    headers = get_auth_headers(client)
    created = client.post(MEDICATIONS_URL, json=make_body(), headers=headers)
    medication_id = created.json()["data"]["id"]

    new_body = make_body()
    new_body["reason"] = "Fever"
    new_body["icon"] = "pill_blue"
    new_body["food_instruction"] = "before_meal"
    new_body["is_active"] = True
    response = client.put(
        MEDICATIONS_URL + "/" + str(medication_id), json=new_body, headers=headers
    )
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["reason"] == "Fever"
    assert data["icon"] == "pill_blue"
    assert data["food_instruction"] == "before_meal"