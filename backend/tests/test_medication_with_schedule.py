from datetime import timedelta

from app.utils.timezone_util import get_today_for_timezone

WIZARD_SAVE_URL = "/medications/with-schedule"
MEDICATIONS_URL = "/medications"
TODAY_URL = "/doses/today"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


def get_today():
    return get_today_for_timezone("Asia/Karachi")


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


def make_daily_schedule():
    # Times are in the wrong order on purpose, the API must sort them
    schedule = {
        "schedule_type": "daily",
        "times": [
            {"time_of_day": "20:00", "dose_amount": 1},
            {"time_of_day": "08:00", "dose_amount": 2},
        ],
    }
    return schedule


def make_body(schedule=None):
    # Returns a fresh dictionary each time
    if schedule is None:
        schedule = make_daily_schedule()
    body = {
        "name": "Wizard Med",
        "dosage": "500 mg",
        "medication_type": "pill",
        "schedule": schedule,
    }
    return body


def get_time_texts(schedule_data):
    texts = []
    for item in schedule_data["times"]:
        texts.append(item["time_of_day"])
    return texts


# ---------------- Saving medicine and schedule together ----------------


def test_create_with_daily_schedule(client):
    headers = get_auth_headers(client)
    response = client.post(WIZARD_SAVE_URL, json=make_body(), headers=headers)
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["message"] == "Medication and schedule saved successfully"

    medication = body["data"]["medication"]
    schedule = body["data"]["schedule"]
    assert medication["name"] == "Wizard Med"
    assert schedule["medication_id"] == medication["id"]
    assert schedule["schedule_type"] == "daily"
    assert get_time_texts(schedule) == ["08:00:00", "20:00:00"]
    assert schedule["times"][0]["dose_amount"] == 2

    # Both must also be readable through the normal endpoints
    medication_id = str(medication["id"])
    get_medication = client.get(MEDICATIONS_URL + "/" + medication_id, headers=headers)
    get_schedule = client.get(
        MEDICATIONS_URL + "/" + medication_id + "/schedule", headers=headers
    )
    assert get_medication.status_code == 200
    assert get_schedule.status_code == 200


def test_create_with_weekly_schedule_sorts_days(client):
    headers = get_auth_headers(client)
    schedule = {
        "schedule_type": "weekly",
        "days_of_week": [4, 0, 2],
        "times": [{"time_of_day": "09:30", "dose_amount": 1}],
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)

    assert response.status_code == 201
    assert response.json()["data"]["schedule"]["days_of_week"] == [0, 2, 4]


def test_create_with_interval_schedule(client):
    headers = get_auth_headers(client)
    schedule = {
        "schedule_type": "interval",
        "interval_days": 2,
        "times": [{"time_of_day": "10:00", "dose_amount": 1}],
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)
    data = response.json()["data"]["schedule"]

    assert response.status_code == 201
    assert data["interval_days"] == 2
    assert data["days_of_week"] is None


# ---------------- Every few hours ----------------


def test_hours_between_eight_creates_three_times(client):
    headers = get_auth_headers(client)
    schedule = {
        "schedule_type": "daily",
        "hours_between": 8,
        "first_dose_time": "06:00",
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)
    data = response.json()["data"]["schedule"]

    assert response.status_code == 201
    assert get_time_texts(data) == ["06:00:00", "14:00:00", "22:00:00"]


def test_hours_between_two_creates_nine_times(client):
    headers = get_auth_headers(client)
    schedule = {
        "schedule_type": "daily",
        "hours_between": 2,
        "first_dose_time": "06:00",
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)
    texts = get_time_texts(response.json()["data"]["schedule"])

    assert response.status_code == 201
    assert len(texts) == 9
    assert texts[0] == "06:00:00"
    assert texts[-1] == "22:00:00"


def test_hours_between_one_creates_24_times(client):
    headers = get_auth_headers(client)
    schedule = {
        "schedule_type": "daily",
        "hours_between": 1,
        "first_dose_time": "00:00",
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)
    texts = get_time_texts(response.json()["data"]["schedule"])

    assert response.status_code == 201
    assert len(texts) == 24


def test_hours_between_without_first_dose_time_fails(client):
    headers = get_auth_headers(client)
    schedule = {"schedule_type": "daily", "hours_between": 8}
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Invalid input data"


def test_times_and_hours_between_together_fail(client):
    headers = get_auth_headers(client)
    schedule = {
        "schedule_type": "daily",
        "times": [{"time_of_day": "08:00", "dose_amount": 1}],
        "hours_between": 8,
        "first_dose_time": "06:00",
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)

    assert response.status_code == 422


def test_missing_times_fails(client):
    headers = get_auth_headers(client)
    schedule = {"schedule_type": "daily"}
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)

    assert response.status_code == 422


def test_schedule_endpoint_also_accepts_hours_between(client):
    headers = get_auth_headers(client)
    medication_body = {
        "name": "Normal Med",
        "dosage": "1 unit",
        "medication_type": "pill",
        "start_date": "2026-11-21",
    }
    created = client.post(MEDICATIONS_URL, json=medication_body, headers=headers)
    medication_id = str(created.json()["data"]["id"])

    schedule = {
        "schedule_type": "daily",
        "hours_between": 12,
        "first_dose_time": "08:00",
    }
    response = client.post(
        MEDICATIONS_URL + "/" + medication_id + "/schedule",
        json=schedule,
        headers=headers,
    )

    assert response.status_code == 201
    assert get_time_texts(response.json()["data"]) == ["08:00:00", "20:00:00"]


# ---------------- Start date and end date ----------------


def test_start_date_defaults_to_today(client):
    headers = get_auth_headers(client)
    response = client.post(WIZARD_SAVE_URL, json=make_body(), headers=headers)
    medication = response.json()["data"]["medication"]

    assert response.status_code == 201
    assert medication["start_date"] == get_today().isoformat()


def test_given_start_date_is_kept(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["start_date"] = "2026-12-01"
    response = client.post(WIZARD_SAVE_URL, json=body, headers=headers)

    assert response.status_code == 201
    assert response.json()["data"]["medication"]["start_date"] == "2026-12-01"


def test_end_date_before_today_fails_when_start_date_is_missing(client):
    headers = get_auth_headers(client)
    body = make_body()
    yesterday = get_today() - timedelta(days=1)
    body["end_date"] = yesterday.isoformat()
    response = client.post(WIZARD_SAVE_URL, json=body, headers=headers)
    result = response.json()

    assert response.status_code == 400
    assert result["success"] is False
    assert result["message"] == "End date cannot be before start date"


# ---------------- Other rules ----------------


def test_invalid_schedule_saves_nothing(client):
    headers = get_auth_headers(client)
    # Weekly schedule without days is invalid
    schedule = {
        "schedule_type": "weekly",
        "times": [{"time_of_day": "09:00", "dose_amount": 1}],
    }
    response = client.post(WIZARD_SAVE_URL, json=make_body(schedule), headers=headers)
    assert response.status_code == 422

    # The medication must not exist either
    list_response = client.get(MEDICATIONS_URL, headers=headers)
    assert len(list_response.json()["data"]) == 0


def test_other_form_needs_a_route(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["medication_type"] = "other"
    missing_route = client.post(WIZARD_SAVE_URL, json=body, headers=headers)
    assert missing_route.status_code == 422

    body["route"] = "ears"
    with_route = client.post(WIZARD_SAVE_URL, json=body, headers=headers)
    assert with_route.status_code == 201
    assert with_route.json()["data"]["medication"]["route"] == "ears"


def test_new_fields_are_saved(client):
    headers = get_auth_headers(client)
    body = make_body()
    body["reason"] = "Headache"
    body["icon"] = "pill_blue"
    body["food_instruction"] = "after_meal"
    response = client.post(WIZARD_SAVE_URL, json=body, headers=headers)
    medication = response.json()["data"]["medication"]

    assert response.status_code == 201
    assert medication["reason"] == "Headache"
    assert medication["icon"] == "pill_blue"
    assert medication["food_instruction"] == "after_meal"


def test_todays_doses_are_created_for_the_new_medication(client):
    headers = get_auth_headers(client)
    client.post(WIZARD_SAVE_URL, json=make_body(), headers=headers)

    response = client.get(TODAY_URL, headers=headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["total"] == 2
    assert data["doses"][0]["medication_name"] == "Wizard Med"


def test_with_schedule_requires_a_token(client):
    response = client.post(WIZARD_SAVE_URL, json=make_body())

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)