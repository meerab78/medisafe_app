REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
PROFILE_URL = "/users/me"


def make_user_data(timezone):
    # Returns a fresh dictionary each time
    user_data = {
        "full_name": "Test User",
        "email": "tz@example.com",
        "password": "test12345",
        "timezone": timezone,
    }
    return user_data


def get_auth_headers(client):
    client.post(REGISTER_URL, json=make_user_data("Asia/Karachi"))
    login_data = {"email": "tz@example.com", "password": "test12345"}
    response = client.post(LOGIN_URL, json=login_data)
    token = response.json()["data"]["access_token"]
    return {"Authorization": "Bearer " + token}


def test_register_with_valid_timezone(client):
    response = client.post(REGISTER_URL, json=make_user_data("Asia/Karachi"))
    body = response.json()

    assert response.status_code == 201
    assert body["data"]["timezone"] == "Asia/Karachi"


def test_register_with_invalid_timezone_fails(client):
    response = client.post(REGISTER_URL, json=make_user_data("abc"))
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"
    assert body["errors"][0]["field"] == "timezone"


def test_register_with_default_timezone_works(client):
    # Timezone is optional, the default is UTC
    user_data = make_user_data("UTC")
    del user_data["timezone"]
    response = client.post(REGISTER_URL, json=user_data)

    assert response.status_code == 201
    assert response.json()["data"]["timezone"] == "UTC"


def test_update_profile_with_valid_timezone(client):
    headers = get_auth_headers(client)
    new_data = {"full_name": "Test User", "timezone": "Europe/London"}
    response = client.put(PROFILE_URL, json=new_data, headers=headers)

    assert response.status_code == 200
    assert response.json()["data"]["timezone"] == "Europe/London"


def test_update_profile_with_invalid_timezone_fails(client):
    headers = get_auth_headers(client)
    new_data = {"full_name": "Test User", "timezone": "Mars/Base"}
    response = client.put(PROFILE_URL, json=new_data, headers=headers)
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["errors"][0]["field"] == "timezone"