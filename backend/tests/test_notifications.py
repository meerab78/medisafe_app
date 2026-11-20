from firebase_admin import exceptions, messaging

from app.core.config import settings
from app.database.connection import get_db
from app.repositories import device_repository
from app.services import notification_service

GOOD_TOKEN_1 = "good-token-one-" + "a" * 40
GOOD_TOKEN_2 = "good-token-two-" + "b" * 40
BAD_TOKEN = "bad-token-" + "c" * 40


def turn_fcm_on(monkeypatch):
    monkeypatch.setattr(settings, "fcm_enabled", True)
    monkeypatch.setattr(notification_service, "get_firebase_app", lambda: None)


def make_fake_send(error=None):
    def fake_send(message):
        if error is not None:
            raise error
        return "projects/test/messages/1"

    return fake_send


def fake_send_with_one_bad_token(message):
    if message.token == BAD_TOKEN:
        raise messaging.UnregisteredError("Token is not registered")
    return "projects/test/messages/1"


def get_test_db(client):
    override_function = client.app.dependency_overrides[get_db]
    db_generator = override_function()
    return next(db_generator)


def create_user_with_devices(client, fcm_tokens):
    user_data = {
        "full_name": "Push User",
        "email": "push@example.com",
        "password": "test12345",
        "timezone": "UTC",
    }
    client.post("/auth/register", json=user_data)
    login_data = {"email": "push@example.com", "password": "test12345"}
    login_response = client.post("/auth/login", json=login_data)
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": "Bearer " + access_token}

    for fcm_token in fcm_tokens:
        body = {"fcm_token": fcm_token, "platform": "android"}
        response = client.post("/devices", json=body, headers=headers)
        assert response.status_code in (200, 201)

    profile_response = client.get("/users/me", headers=headers)
    return profile_response.json()["data"]["id"]


def test_send_is_skipped_when_fcm_is_disabled(monkeypatch):
    monkeypatch.setattr(settings, "fcm_enabled", False)
    result = notification_service.send_push_to_token("any-token", "Title", "Body")
    assert result == "disabled"


def test_send_success(monkeypatch):
    turn_fcm_on(monkeypatch)
    monkeypatch.setattr(notification_service.messaging, "send", make_fake_send())
    result = notification_service.send_push_to_token("any-token", "Title", "Body")
    assert result == "sent"


def test_unregistered_token_is_reported_as_invalid(monkeypatch):
    turn_fcm_on(monkeypatch)
    error = messaging.UnregisteredError("Token is not registered")
    monkeypatch.setattr(notification_service.messaging, "send", make_fake_send(error))
    result = notification_service.send_push_to_token("any-token", "Title", "Body")
    assert result == "invalid_token"


def test_other_firebase_error_is_reported_as_failed(monkeypatch):
    turn_fcm_on(monkeypatch)
    error = exceptions.UnavailableError("FCM is down")
    monkeypatch.setattr(notification_service.messaging, "send", make_fake_send(error))
    result = notification_service.send_push_to_token("any-token", "Title", "Body")
    assert result == "failed"


def test_send_to_user_counts_sent_messages(client, monkeypatch):
    turn_fcm_on(monkeypatch)
    monkeypatch.setattr(notification_service.messaging, "send", make_fake_send())
    user_id = create_user_with_devices(client, [GOOD_TOKEN_1, GOOD_TOKEN_2])

    db = get_test_db(client)
    sent_count = notification_service.send_push_to_user(db, user_id, "Title", "Body")
    db.close()

    assert sent_count == 2


def test_send_to_user_removes_invalid_tokens(client, monkeypatch):
    turn_fcm_on(monkeypatch)
    monkeypatch.setattr(
        notification_service.messaging, "send", fake_send_with_one_bad_token
    )
    user_id = create_user_with_devices(client, [GOOD_TOKEN_1, BAD_TOKEN])

    db = get_test_db(client)
    sent_count = notification_service.send_push_to_user(db, user_id, "Title", "Body")
    remaining_tokens = device_repository.list_fcm_tokens_for_user(db, user_id)
    db.close()

    assert sent_count == 1
    assert remaining_tokens == [GOOD_TOKEN_1]