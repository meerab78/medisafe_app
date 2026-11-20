from datetime import timedelta

from app.utils.timezone_util import get_today_for_timezone

MEDICATIONS_URL = "/medications"
TODAY_URL = "/doses/today"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


def get_today():
    return get_today_for_timezone("Asia/Karachi")


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


def add_medication(client, headers, start_date=None, end_date=None):
    if start_date is None:
        start_date = get_today()
    body = {
        "name": "Paracetamol",
        "dosage": "500 mg",
        "medication_type": "tablet",
        "start_date": start_date.isoformat(),
    }
    if end_date is not None:
        body["end_date"] = end_date.isoformat()
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)
    return response.json()["data"]["id"]


def schedule_url(medication_id):
    return MEDICATIONS_URL + "/" + str(medication_id) + "/schedule"


def add_schedule(client, headers, medication_id, body):
    return client.post(schedule_url(medication_id), json=body, headers=headers)


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


def make_one_time_body(schedule_type, days_of_week=None, interval_days=None):
    body = {
        "schedule_type": schedule_type,
        "times": [{"time_of_day": "09:00", "dose_amount": 1}],
    }
    if days_of_week is not None:
        body["days_of_week"] = days_of_week
    if interval_days is not None:
        body["interval_days"] = interval_days
    return body


def get_today_data(client, headers):
    response = client.get(TODAY_URL, headers=headers)
    return response.json()["data"]


def dose_url(dose_id, action):
    return "/doses/" + str(dose_id) + "/" + action


# ---------------- Generating today's doses ----------------


def test_today_is_empty_when_no_schedules(client):
    headers = get_auth_headers(client)
    add_medication(client, headers)

    response = client.get(TODAY_URL, headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["total"] == 0
    assert body["data"]["doses"] == []


def test_daily_schedule_creates_doses_for_today(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())

    response = client.get(TODAY_URL, headers=headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["day"] == get_today().isoformat()
    assert data["timezone"] == "Asia/Karachi"
    assert data["total"] == 2
    assert data["pending"] == 2
    assert data["doses"][0]["time_of_day"] == "08:00:00"
    assert data["doses"][0]["dose_amount"] == 2
    assert data["doses"][0]["medication_name"] == "Paracetamol"
    assert data["doses"][0]["status"] == "pending"
    assert data["doses"][1]["time_of_day"] == "20:00:00"


def test_calling_today_twice_does_not_create_duplicates(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())

    client.get(TODAY_URL, headers=headers)
    data = get_today_data(client, headers)

    assert data["total"] == 2


def test_weekly_schedule_on_another_day_creates_no_doses(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    other_day = (get_today().weekday() + 1) % 7
    body = make_one_time_body("weekly", days_of_week=[other_day])
    add_schedule(client, headers, medication_id, body)

    data = get_today_data(client, headers)

    assert data["total"] == 0


def test_weekly_schedule_on_today_creates_a_dose(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    body = make_one_time_body("weekly", days_of_week=[get_today().weekday()])
    add_schedule(client, headers, medication_id, body)

    data = get_today_data(client, headers)

    assert data["total"] == 1


def test_interval_schedule_on_off_day_creates_no_doses(client):
    headers = get_auth_headers(client)
    # Started yesterday, every 2 days, so today is an off day
    start_date = get_today() - timedelta(days=1)
    medication_id = add_medication(client, headers, start_date=start_date)
    body = make_one_time_body("interval", interval_days=2)
    add_schedule(client, headers, medication_id, body)

    data = get_today_data(client, headers)

    assert data["total"] == 0


def test_interval_schedule_on_due_day_creates_a_dose(client):
    headers = get_auth_headers(client)
    # Started 2 days ago, every 2 days, so today is a due day
    start_date = get_today() - timedelta(days=2)
    medication_id = add_medication(client, headers, start_date=start_date)
    body = make_one_time_body("interval", interval_days=2)
    add_schedule(client, headers, medication_id, body)

    data = get_today_data(client, headers)

    assert data["total"] == 1


def test_future_medication_creates_no_doses(client):
    headers = get_auth_headers(client)
    start_date = get_today() + timedelta(days=1)
    medication_id = add_medication(client, headers, start_date=start_date)
    add_schedule(client, headers, medication_id, make_daily_body())

    data = get_today_data(client, headers)

    assert data["total"] == 0


def test_finished_medication_creates_no_doses(client):
    headers = get_auth_headers(client)
    start_date = get_today() - timedelta(days=10)
    end_date = get_today() - timedelta(days=1)
    medication_id = add_medication(
        client, headers, start_date=start_date, end_date=end_date
    )
    add_schedule(client, headers, medication_id, make_daily_body())

    data = get_today_data(client, headers)

    assert data["total"] == 0


def test_deleted_medication_doses_are_hidden(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())

    before = get_today_data(client, headers)
    assert before["total"] == 2

    client.delete(MEDICATIONS_URL + "/" + str(medication_id), headers=headers)
    after = get_today_data(client, headers)

    assert after["total"] == 0


def test_updating_schedule_replaces_todays_pending_doses(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())

    before = get_today_data(client, headers)
    assert before["total"] == 2

    new_body = {
        "schedule_type": "daily",
        "times": [{"time_of_day": "12:00", "dose_amount": 1}],
    }
    client.put(schedule_url(medication_id), json=new_body, headers=headers)
    after = get_today_data(client, headers)

    assert after["total"] == 1
    assert after["doses"][0]["time_of_day"] == "12:00:00"


# ---------------- Take and skip ----------------


def test_take_dose_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())
    data = get_today_data(client, headers)
    dose_id = data["doses"][0]["id"]

    response = client.put(dose_url(dose_id, "take"), headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Dose marked as taken"
    assert body["data"]["status"] == "taken"
    assert body["data"]["taken_at"] is not None


def test_take_dose_twice_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())
    data = get_today_data(client, headers)
    dose_id = data["doses"][0]["id"]

    client.put(dose_url(dose_id, "take"), headers=headers)
    response = client.put(dose_url(dose_id, "take"), headers=headers)
    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["message"] == "This dose is already marked as taken"


def test_skip_dose_success(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())
    data = get_today_data(client, headers)
    dose_id = data["doses"][0]["id"]

    response = client.put(dose_url(dose_id, "skip"), headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Dose marked as skipped"
    assert body["data"]["status"] == "skipped"
    assert body["data"]["taken_at"] is None


def test_take_after_skip_fails(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())
    data = get_today_data(client, headers)
    dose_id = data["doses"][0]["id"]

    client.put(dose_url(dose_id, "skip"), headers=headers)
    response = client.put(dose_url(dose_id, "take"), headers=headers)

    assert response.status_code == 400
    assert response.json()["message"] == "This dose is already marked as skipped"


def test_today_counts_after_taking_one_dose(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    add_schedule(client, headers, medication_id, make_daily_body())
    data = get_today_data(client, headers)
    dose_id = data["doses"][0]["id"]

    client.put(dose_url(dose_id, "take"), headers=headers)
    after = get_today_data(client, headers)

    assert after["total"] == 2
    assert after["taken"] == 1
    assert after["pending"] == 1


def test_take_unknown_dose_returns_404(client):
    headers = get_auth_headers(client)
    response = client.put(dose_url(9999, "take"), headers=headers)
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["message"] == "Dose not found"


# ---------------- Ownership and token ----------------


def test_other_user_cannot_take_my_dose(client):
    my_headers = get_auth_headers(client)
    medication_id = add_medication(client, my_headers)
    add_schedule(client, my_headers, medication_id, make_daily_body())
    data = get_today_data(client, my_headers)
    dose_id = data["doses"][0]["id"]

    other_headers = get_other_user_headers(client)
    response = client.put(dose_url(dose_id, "take"), headers=other_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Dose not found"

    # My dose must still be pending
    check = get_today_data(client, my_headers)
    assert check["pending"] == 2


def test_other_user_today_does_not_show_my_doses(client):
    my_headers = get_auth_headers(client)
    medication_id = add_medication(client, my_headers)
    add_schedule(client, my_headers, medication_id, make_daily_body())
    get_today_data(client, my_headers)

    other_headers = get_other_user_headers(client)
    data = get_today_data(client, other_headers)

    assert data["total"] == 0


def test_today_without_token_fails(client):
    response = client.get(TODAY_URL)

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)