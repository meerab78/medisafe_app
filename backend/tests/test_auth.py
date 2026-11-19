REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
PROFILE_URL = "/users/me"
PASSWORD_URL = "/users/me/password"

USER_DATA = {
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "test12345",
    "timezone": "Asia/Karachi",
}


def register_test_user(client):
    return client.post(REGISTER_URL, json=USER_DATA)


def login_test_user(client, password="test12345"):
    return client.post(
        LOGIN_URL, json={"email": USER_DATA["email"], "password": password}
    )


def get_auth_headers(client):
    register_test_user(client)
    response = login_test_user(client)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_success(client):
    response = register_test_user(client)
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["data"]["email"] == "test@example.com"
    assert "password" not in body["data"]
    assert "hashed_password" not in body["data"]


def test_register_duplicate_email_fails(client):
    register_test_user(client)
    response = register_test_user(client)
    body = response.json()

    assert response.status_code == 409
    assert body["success"] is False
    assert body["message"] == "Email is already registered"


def test_register_email_is_case_insensitive(client):
    register_test_user(client)
    other_case = {**USER_DATA, "email": "TEST@Example.com"}
    response = client.post(REGISTER_URL, json=other_case)

    assert response.status_code == 409


def test_register_short_password_fails(client):
    short_password = {**USER_DATA, "password": "123"}
    response = client.post(REGISTER_URL, json=short_password)
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"
    assert body["errors"][0]["field"] == "password"


def test_login_success_returns_token(client):
    register_test_user(client)
    response = login_test_user(client)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["access_token"]


def test_login_wrong_password_fails(client):
    register_test_user(client)
    response = login_test_user(client, password="wrongpass1")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["message"] == "Incorrect email or password"


def test_profile_with_valid_token(client):
    headers = get_auth_headers(client)
    response = client.get(PROFILE_URL, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["email"] == "test@example.com"


def test_profile_without_token_fails(client):
    response = client.get(PROFILE_URL)

    assert response.status_code in (401, 403)
    assert response.json()["success"] is False


def test_profile_with_invalid_token_fails(client):
    headers = {"Authorization": "Bearer this.is.not.valid"}
    response = client.get(PROFILE_URL, headers=headers)

    assert response.status_code == 401
    assert response.json()["success"] is False


def test_update_profile(client):
    headers = get_auth_headers(client)
    new_data = {"full_name": "New Name", "timezone": "UTC"}
    response = client.put(PROFILE_URL, json=new_data, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["full_name"] == "New Name"


def test_change_password_flow(client):
    headers = get_auth_headers(client)

    wrong_current = {"current_password": "wrongpass1", "new_password": "newpass123"}
    response = client.put(PASSWORD_URL, json=wrong_current, headers=headers)
    assert response.status_code == 400
    assert response.json()["success"] is False

    correct_current = {"current_password": "test12345", "new_password": "newpass123"}
    response = client.put(PASSWORD_URL, json=correct_current, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    assert login_test_user(client, password="test12345").status_code == 401
    assert login_test_user(client, password="newpass123").status_code == 200