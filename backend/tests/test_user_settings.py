SETTINGS_URL = "/settings"
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


def make_body():
    # Returns a fresh dictionary each time
    body = {
        "reminders_enabled": False,
        "snooze_minutes": 15,
        "refill_alerts_enabled": False,
    }
    return body


def test_get_settings_creates_defaults(client):
    headers = get_auth_headers(client)
    response = client.get(SETTINGS_URL, headers=headers)
    body = response.json()
    data = body["data"]

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Settings fetched successfully"
    assert data["reminders_enabled"] is True
    assert data["snooze_minutes"] == 10
    assert data["refill_alerts_enabled"] is True
    assert data["snooze_options"] == [5, 10, 15, 30, 60]


def test_get_settings_twice_gives_the_same_result(client):
    headers = get_auth_headers(client)
    first = client.get(SETTINGS_URL, headers=headers)
    second = client.get(SETTINGS_URL, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


def test_update_settings_and_read_them_back(client):
    headers = get_auth_headers(client)
    client.get(SETTINGS_URL, headers=headers)

    response = client.put(SETTINGS_URL, json=make_body(), headers=headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert response.json()["message"] == "Settings updated successfully"
    assert data["reminders_enabled"] is False
    assert data["snooze_minutes"] == 15
    assert data["refill_alerts_enabled"] is False

    check = client.get(SETTINGS_URL, headers=headers)
    assert check.json()["data"]["snooze_minutes"] == 15
    assert check.json()["data"]["reminders_enabled"] is False


def test_update_works_before_the_first_get(client):
    headers = get_auth_headers(client)
    response = client.put(SETTINGS_URL, json=make_body(), headers=headers)

    assert response.status_code == 200
    assert response.json()["data"]["snooze_minutes"] == 15


def test_every_snooze_option_is_accepted(client):
    headers = get_auth_headers(client)

    for value in [5, 10, 15, 30, 60]:
        body = make_body()
        body["snooze_minutes"] = value
        response = client.put(SETTINGS_URL, json=body, headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["snooze_minutes"] == value


def test_invalid_snooze_minutes_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["snooze_minutes"] = 7
    response = client.put(SETTINGS_URL, json=body, headers=headers)
    result = response.json()

    assert response.status_code == 422
    assert result["success"] is False
    assert result["message"] == "Invalid input data"
    assert result["errors"][0]["field"] == "snooze_minutes"


def test_missing_field_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    del body["refill_alerts_enabled"]
    response = client.put(SETTINGS_URL, json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "refill_alerts_enabled"


def test_each_user_has_their_own_settings(client):
    my_headers = get_auth_headers(client)
    client.put(SETTINGS_URL, json=make_body(), headers=my_headers)

    other_headers = get_other_user_headers(client)
    response = client.get(SETTINGS_URL, headers=other_headers)
    data = response.json()["data"]

    # The other user still has the defaults
    assert data["snooze_minutes"] == 10
    assert data["reminders_enabled"] is True


def test_settings_without_token_fail(client):
    get_response = client.get(SETTINGS_URL)
    put_response = client.put(SETTINGS_URL, json=make_body())

    # Depending on the FastAPI version this is 401 or 403
    assert get_response.status_code in (401, 403)
    assert put_response.status_code in (401, 403)