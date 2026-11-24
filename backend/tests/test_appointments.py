from datetime import timedelta

from app.core.appointment_options import APPOINTMENT_REMINDERS
from app.schemas.appointment_schema import AppointmentCreate
from app.utils.timezone_util import get_today_for_timezone

APPOINTMENTS_URL = "/appointments"
WIZARD_URL = "/options/appointment-wizard"
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


def make_time_text(days_from_today, clock="16:30:00"):
    # Example: 2026-12-23T16:30:00 (the user's local time)
    day = get_today_for_timezone("Asia/Karachi") + timedelta(days=days_from_today)
    return day.isoformat() + "T" + clock


def make_body(days_from_today=30, title="Dentist visit"):
    # Returns a fresh dictionary each time
    body = {
        "title": title,
        "doctor_name": "Dr. Ahmed",
        "location": "City Hospital",
        "appointment_at": make_time_text(days_from_today),
        "remind_before_minutes": 60,
        "notes": "Bring old X-ray report",
    }
    return body


def add_appointment(client, headers, body=None):
    if body is None:
        body = make_body()
    return client.post(APPOINTMENTS_URL, json=body, headers=headers)


def get_titles(response):
    titles = []
    for item in response.json()["data"]:
        titles.append(item["title"])
    return titles


# ---------------- Create ----------------


def test_create_appointment_success(client):
    headers = get_auth_headers(client)
    response = add_appointment(client, headers)
    body = response.json()
    data = body["data"]

    assert response.status_code == 201
    assert body["success"] is True
    assert body["message"] == "Appointment saved successfully"
    assert data["title"] == "Dentist visit"
    assert data["doctor_name"] == "Dr. Ahmed"
    assert data["location"] == "City Hospital"
    assert data["remind_before_minutes"] == 60
    assert data["notes"] == "Bring old X-ray report"
    # The time comes back in the user's own timezone (Karachi is +05:00)
    assert data["appointment_at"].startswith(make_time_text(30))
    assert data["appointment_at"].endswith("+05:00")


def test_create_with_only_required_fields(client):
    headers = get_auth_headers(client)
    body = {"title": "Eye test", "appointment_at": make_time_text(10)}
    response = add_appointment(client, headers, body)
    data = response.json()["data"]

    assert response.status_code == 201
    assert data["doctor_name"] is None
    assert data["location"] is None
    assert data["notes"] is None
    assert data["remind_before_minutes"] is None


def test_all_reminder_options_are_accepted(client):
    headers = get_auth_headers(client)

    for value in [30, 60, 720, 10080]:
        body = make_body()
        body["remind_before_minutes"] = value
        response = add_appointment(client, headers, body)
        assert response.status_code == 201
        assert response.json()["data"]["remind_before_minutes"] == value

    # 0 means "no reminder" and is saved as null
    body = make_body()
    body["remind_before_minutes"] = 0
    response = add_appointment(client, headers, body)
    assert response.status_code == 201
    assert response.json()["data"]["remind_before_minutes"] is None


def test_invalid_reminder_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["remind_before_minutes"] = 45
    response = add_appointment(client, headers, body)
    result = response.json()

    assert response.status_code == 422
    assert result["success"] is False
    assert result["message"] == "Invalid input data"
    assert result["errors"][0]["field"] == "remind_before_minutes"


def test_empty_title_fails(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["title"] = "   "
    response = add_appointment(client, headers, body)

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "title"


def test_past_appointment_fails(client):
    headers = get_auth_headers(client)
    response = add_appointment(client, headers, make_body(days_from_today=-1))
    result = response.json()

    assert response.status_code == 400
    assert result["success"] is False
    assert result["message"] == "Appointment time must be in the future"


def test_missing_date_fails(client):
    headers = get_auth_headers(client)
    response = client.post(
        APPOINTMENTS_URL, json={"title": "No date"}, headers=headers
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "appointment_at"


def test_create_appointment_without_token_fails(client):
    response = client.post(APPOINTMENTS_URL, json=make_body())

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)


# ---------------- List ----------------


def test_list_shows_upcoming_sorted_by_time(client):
    headers = get_auth_headers(client)
    add_appointment(client, headers, make_body(days_from_today=40, title="Later"))
    add_appointment(client, headers, make_body(days_from_today=20, title="Sooner"))

    response = client.get(APPOINTMENTS_URL, headers=headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert get_titles(response) == ["Sooner", "Later"]


def test_list_past_and_all(client):
    headers = get_auth_headers(client)
    created = add_appointment(client, headers, make_body(days_from_today=10))
    appointment_id = str(created.json()["data"]["id"])

    # Moving an appointment to the past is allowed in update
    past_body = make_body(days_from_today=-5)
    update = client.put(
        APPOINTMENTS_URL + "/" + appointment_id, json=past_body, headers=headers
    )
    assert update.status_code == 200

    upcoming = client.get(APPOINTMENTS_URL, headers=headers)
    past = client.get(APPOINTMENTS_URL, params={"when": "past"}, headers=headers)
    everything = client.get(APPOINTMENTS_URL, params={"when": "all"}, headers=headers)

    assert len(upcoming.json()["data"]) == 0
    assert len(past.json()["data"]) == 1
    assert len(everything.json()["data"]) == 1


def test_invalid_when_value_fails(client):
    headers = get_auth_headers(client)
    response = client.get(APPOINTMENTS_URL, params={"when": "tomorrow"}, headers=headers)

    assert response.status_code == 422


# ---------------- Get, update, delete ----------------


def test_get_appointment_success(client):
    headers = get_auth_headers(client)
    created = add_appointment(client, headers)
    appointment_id = str(created.json()["data"]["id"])

    response = client.get(APPOINTMENTS_URL + "/" + appointment_id, headers=headers)

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Dentist visit"


def test_get_appointment_not_found(client):
    headers = get_auth_headers(client)
    response = client.get(APPOINTMENTS_URL + "/9999", headers=headers)
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["message"] == "Appointment not found"


def test_update_appointment_success(client):
    headers = get_auth_headers(client)
    created = add_appointment(client, headers)
    appointment_id = str(created.json()["data"]["id"])

    new_body = make_body(days_from_today=45, title="Dentist follow-up")
    new_body["remind_before_minutes"] = 720
    new_body["notes"] = "Ask about braces"
    response = client.put(
        APPOINTMENTS_URL + "/" + appointment_id, json=new_body, headers=headers
    )
    data = response.json()["data"]

    assert response.status_code == 200
    assert response.json()["message"] == "Appointment updated successfully"
    assert data["title"] == "Dentist follow-up"
    assert data["remind_before_minutes"] == 720
    assert data["notes"] == "Ask about braces"
    assert data["appointment_at"].startswith(make_time_text(45))


def test_update_to_no_reminder(client):
    headers = get_auth_headers(client)
    created = add_appointment(client, headers)
    appointment_id = str(created.json()["data"]["id"])

    new_body = make_body()
    new_body["remind_before_minutes"] = 0
    response = client.put(
        APPOINTMENTS_URL + "/" + appointment_id, json=new_body, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["remind_before_minutes"] is None


def test_delete_appointment_success(client):
    headers = get_auth_headers(client)
    created = add_appointment(client, headers)
    appointment_id = str(created.json()["data"]["id"])

    response = client.delete(APPOINTMENTS_URL + "/" + appointment_id, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Appointment deleted successfully"

    check = client.get(APPOINTMENTS_URL + "/" + appointment_id, headers=headers)
    assert check.status_code == 404


# ---------------- Ownership (other user) ----------------


def test_other_user_cannot_get_my_appointment(client):
    my_headers = get_auth_headers(client)
    created = add_appointment(client, my_headers)
    appointment_id = str(created.json()["data"]["id"])

    other_headers = get_other_user_headers(client)
    response = client.get(APPOINTMENTS_URL + "/" + appointment_id, headers=other_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Appointment not found"


def test_other_user_cannot_update_my_appointment(client):
    my_headers = get_auth_headers(client)
    created = add_appointment(client, my_headers)
    appointment_id = str(created.json()["data"]["id"])

    other_headers = get_other_user_headers(client)
    new_body = make_body(title="Hacked")
    response = client.put(
        APPOINTMENTS_URL + "/" + appointment_id, json=new_body, headers=other_headers
    )
    assert response.status_code == 404

    # The original must stay unchanged
    check = client.get(APPOINTMENTS_URL + "/" + appointment_id, headers=my_headers)
    assert check.json()["data"]["title"] == "Dentist visit"


def test_other_user_cannot_delete_my_appointment(client):
    my_headers = get_auth_headers(client)
    created = add_appointment(client, my_headers)
    appointment_id = str(created.json()["data"]["id"])

    other_headers = get_other_user_headers(client)
    response = client.delete(
        APPOINTMENTS_URL + "/" + appointment_id, headers=other_headers
    )
    assert response.status_code == 404

    # My appointment must still be there
    check = client.get(APPOINTMENTS_URL + "/" + appointment_id, headers=my_headers)
    assert check.status_code == 200


def test_other_user_list_does_not_show_my_appointments(client):
    my_headers = get_auth_headers(client)
    add_appointment(client, my_headers)

    other_headers = get_other_user_headers(client)
    response = client.get(APPOINTMENTS_URL, headers=other_headers)

    assert response.status_code == 200
    assert len(response.json()["data"]) == 0


# ---------------- Appointment wizard options ----------------


def get_wizard_steps(client):
    response = client.get(WIZARD_URL)
    return response.json()["data"]["steps"]


def test_appointment_wizard_is_public_with_expected_steps(client):
    # No token is sent on purpose
    response = client.get(WIZARD_URL)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Appointment wizard fetched successfully"

    ids = []
    for step in body["data"]["steps"]:
        ids.append(step["id"])
    assert ids == [
        "title",
        "appointment_at",
        "remind_before_minutes",
        "doctor_name",
        "location",
        "notes",
    ]


def test_wizard_reminder_options(client):
    steps = get_wizard_steps(client)
    reminder_step = steps[2]

    values = []
    labels = []
    for option in reminder_step["options"]:
        values.append(option["value"])
        labels.append(option["label"])

    assert values == [30, 60, 720, 10080, 0]
    assert labels[0] == "30 minutes before"
    assert labels[1] == "1 hour before"
    assert labels[2] == "12 hours before"
    assert labels[3] == "1 week before"
    assert labels[4] == "No reminder"


def test_every_wizard_reminder_is_accepted_by_the_server(client):
    headers = get_auth_headers(client)

    for option in APPOINTMENT_REMINDERS:
        body = make_body()
        body["remind_before_minutes"] = option["value"]
        response = add_appointment(client, headers, body)
        assert response.status_code == 201


def test_wizard_fields_exist_in_the_appointment_schema(client):
    steps = get_wizard_steps(client)

    for step in steps:
        assert step["field"] in AppointmentCreate.model_fields