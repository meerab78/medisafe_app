DEVICES_URL = "/devices"
UNREGISTER_URL = "/devices/unregister"
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


def register_device(client, headers, fcm_token="fcm-token-for-test-0001", platform="android"):
    body = {"fcm_token": fcm_token, "platform": platform}
    return client.post(DEVICES_URL, json=body, headers=headers)


def get_device_list(client, headers):
    response = client.get(DEVICES_URL, headers=headers)
    return response.json()["data"]


def test_register_device_success(client):
    headers = get_auth_headers(client)
    response = register_device(client, headers)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Device registered successfully"
    assert body["data"]["platform"] == "android"
    assert "fcm_token" not in body["data"]


def test_register_same_token_twice_keeps_one_device(client):
    headers = get_auth_headers(client)
    register_device(client, headers, platform="android")
    register_device(client, headers, platform="ios")

    devices = get_device_list(client, headers)

    assert len(devices) == 1
    assert devices[0]["platform"] == "ios"


def test_same_token_moves_to_the_new_user(client):
    first_headers = get_auth_headers(client)
    register_device(client, first_headers)

    second_headers = get_other_user_headers(client)
    register_device(client, second_headers)

    assert len(get_device_list(client, first_headers)) == 0
    assert len(get_device_list(client, second_headers)) == 1


def test_invalid_platform_fails(client):
    headers = get_auth_headers(client)
    response = register_device(client, headers, platform="windows")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"
    assert body["errors"][0]["field"] == "platform"


def test_short_token_fails(client):
    headers = get_auth_headers(client)
    response = register_device(client, headers, fcm_token="abc")

    assert response.status_code == 422


def test_list_shows_only_my_devices(client):
    my_headers = get_auth_headers(client)
    register_device(client, my_headers, fcm_token="fcm-token-for-test-0001")

    other_headers = get_other_user_headers(client)
    register_device(client, other_headers, fcm_token="fcm-token-for-test-0002")

    assert len(get_device_list(client, my_headers)) == 1
    assert len(get_device_list(client, other_headers)) == 1


def test_unregister_device_success(client):
    headers = get_auth_headers(client)
    register_device(client, headers)

    body = {"fcm_token": "fcm-token-for-test-0001"}
    response = client.post(UNREGISTER_URL, json=body, headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Device removed successfully"
    assert len(get_device_list(client, headers)) == 0


def test_unregister_unknown_token_returns_404(client):
    headers = get_auth_headers(client)

    body = {"fcm_token": "fcm-token-that-does-not-exist"}
    response = client.post(UNREGISTER_URL, json=body, headers=headers)
    result = response.json()

    assert response.status_code == 404
    assert result["success"] is False
    assert result["message"] == "Device not found"


def test_other_user_cannot_unregister_my_device(client):
    my_headers = get_auth_headers(client)
    register_device(client, my_headers)

    other_headers = get_other_user_headers(client)
    body = {"fcm_token": "fcm-token-for-test-0001"}
    response = client.post(UNREGISTER_URL, json=body, headers=other_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Device not found"

    # My device must still be there
    assert len(get_device_list(client, my_headers)) == 1


def test_devices_without_token_fails(client):
    response = client.get(DEVICES_URL)

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)