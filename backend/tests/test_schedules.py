MEDICATIONS_URL = "/medications"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


def get_headers_for(client, email):
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
    return get_headers_for(client, "test@example.com")


def get_other_user_headers(client):
    return get_headers_for(client, "other@example.com")


def add_medication(client, headers):
    body = {
        "name": "Paracetamol",
        "dosage": "500 mg",
        "medication_type": "pill",
        "start_date": "2026-11-20",
    }
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)
    return response.json()["data"]["id"]


def schedule_url(medication_id):
    return MEDICATIONS_URL + "/" + str(medication_id) + "/schedule"


def make_daily_body():
    # Times are given in the wrong order on purpose, the API must sort them
    body = {
        "schedule_type": "daily",
        "times": [
            {"time_of_day": "20:00", "dose_amount": 1},
            {"time_of_day": "08:00", "dose_amount": 2},
        ],
    }
    return body


# ---------------- Create ----------------


def test_create_daily_schedule_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    response = client.post(
        schedule_url(medication_id), json=make_daily_body(), headers=headers
    )
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["message"] == "Schedule created successfully"
    assert body["data"]["schedule_type"] == "daily"
    assert body["data"]["days_of_week"] is None
    assert len(body["data"]["times"]) == 2
    assert body["data"]["times"][0]["time_of_day"] == "08:00:00"
    assert body["data"]["times"][0]["dose_amount"] == 2
    assert body["data"]["times"][1]["time_of_day"] == "20:00:00"


def test_create_weekly_schedule_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {
        "schedule_type": "weekly",
        "days_of_week": [4, 0, 2],
        "times": [{"time_of_day": "09:30", "dose_amount": 1}],
    }
    response = client.post(schedule_url(medication_id), json=data, headers=headers)
    body = response.json()

    assert response.status_code == 201
    assert body["data"]["days_of_week"] == [0, 2, 4]


def test_create_interval_schedule_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {
        "schedule_type": "interval",
        "interval_days": 2,
        "times": [{"time_of_day": "10:00", "dose_amount": 1}],
    }
    response = client.post(schedule_url(medication_id), json=data, headers=headers)
    body = response.json()

    assert response.status_code == 201
    assert body["data"]["interval_days"] == 2
    assert body["data"]["days_of_week"] is None


def test_weekly_without_days_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {
        "schedule_type": "weekly",
        "times": [{"time_of_day": "09:00", "dose_amount": 1}],
    }
    response = client.post(schedule_url(medication_id), json=data, headers=headers)
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"


def test_weekly_with_invalid_day_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {
        "schedule_type": "weekly",
        "days_of_week": [0, 7],
        "times": [{"time_of_day": "09:00", "dose_amount": 1}],
    }
    response = client.post(schedule_url(medication_id), json=data, headers=headers)

    assert response.status_code == 422


def test_interval_without_interval_days_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {
        "schedule_type": "interval",
        "times": [{"time_of_day": "09:00", "dose_amount": 1}],
    }
    response = client.post(schedule_url(medication_id), json=data, headers=headers)

    assert response.status_code == 422


def test_invalid_schedule_type_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = make_daily_body()
    data["schedule_type"] = "monthly"
    response = client.post(schedule_url(medication_id), json=data, headers=headers)
    body = response.json()

    assert response.status_code == 422
    assert body["errors"][0]["field"] == "schedule_type"


def test_empty_times_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {"schedule_type": "daily", "times": []}
    response = client.post(schedule_url(medication_id), json=data, headers=headers)

    assert response.status_code == 422


def test_duplicate_times_fail(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    data = {
        "schedule_type": "daily",
        "times": [
            {"time_of_day": "08:00", "dose_amount": 1},
            {"time_of_day": "08:00", "dose_amount": 1},
        ],
    }
    response = client.post(schedule_url(medication_id), json=data, headers=headers)

    assert response.status_code == 422


def test_create_schedule_twice_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    client.post(schedule_url(medication_id), json=make_daily_body(), headers=headers)
    response = client.post(
        schedule_url(medication_id), json=make_daily_body(), headers=headers
    )
    body = response.json()

    assert response.status_code == 409
    assert body["success"] is False
    assert body["message"] == "This medication already has a schedule"


def test_create_schedule_for_missing_medication_fails(client):
    headers = get_auth_headers(client)
    response = client.post(schedule_url(9999), json=make_daily_body(), headers=headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Medication not found"


def test_schedule_without_token_fails(client):
    response = client.get(schedule_url(1))

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)


# ---------------- Get ----------------


def test_get_schedule_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    client.post(schedule_url(medication_id), json=make_daily_body(), headers=headers)

    response = client.get(schedule_url(medication_id), headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["schedule_type"] == "daily"
    assert len(body["data"]["times"]) == 2


def test_get_schedule_when_none_exists(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)

    response = client.get(schedule_url(medication_id), headers=headers)
    body = response.json()

    assert response.status_code == 404
    assert body["message"] == "Schedule not found"


# ---------------- Update and delete ----------------


def test_update_schedule_replaces_everything(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    client.post(schedule_url(medication_id), json=make_daily_body(), headers=headers)

    new_data = {
        "schedule_type": "weekly",
        "days_of_week": [1, 3],
        "times": [{"time_of_day": "07:00", "dose_amount": 1}],
    }
    response = client.put(schedule_url(medication_id), json=new_data, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Schedule updated successfully"
    assert body["data"]["schedule_type"] == "weekly"
    assert body["data"]["days_of_week"] == [1, 3]
    assert len(body["data"]["times"]) == 1
    assert body["data"]["times"][0]["time_of_day"] == "07:00:00"


def test_delete_schedule_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    client.post(schedule_url(medication_id), json=make_daily_body(), headers=headers)

    response = client.delete(schedule_url(medication_id), headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Schedule deleted successfully"

    check = client.get(schedule_url(medication_id), headers=headers)
    assert check.status_code == 404


# ---------------- Ownership (other user) ----------------


def test_other_user_cannot_create_schedule(client):
    my_headers = get_auth_headers(client)
    medication_id = add_medication(client, my_headers)

    other_headers = get_other_user_headers(client)
    response = client.post(
        schedule_url(medication_id), json=make_daily_body(), headers=other_headers
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Medication not found"


def test_other_user_cannot_get_my_schedule(client):
    my_headers = get_auth_headers(client)
    medication_id = add_medication(client, my_headers)
    client.post(
        schedule_url(medication_id), json=make_daily_body(), headers=my_headers
    )

    other_headers = get_other_user_headers(client)
    response = client.get(schedule_url(medication_id), headers=other_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Medication not found"