from datetime import date, datetime, timedelta, timezone

from app.database.connection import get_db
from app.models.dose_log_model import DoseLog
from app.models.medication_model import Medication


def get_test_db(client):
    override_function = client.app.dependency_overrides[get_db]
    db_generator = override_function()
    return next(db_generator)


def register_and_login(client, email="report@example.com"):
    user_data = {
        "full_name": "Report User",
        "email": email,
        "password": "test12345",
        "timezone": "UTC",
    }
    client.post("/auth/register", json=user_data)
    login_data = {"email": email, "password": "test12345"}
    login_response = client.post("/auth/login", json=login_data)
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    profile_response = client.get("/users/me", headers=headers)
    user_id = profile_response.json()["data"]["id"]
    return headers, user_id


def add_medication(db, user_id, name="Metformin"):
    medication = Medication(
        user_id=user_id,
        name=name,
        dosage="500 mg",
        medication_type="tablet",
        start_date=date(2026, 1, 1),
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return medication


def add_dose(db, medication_id, day, status_text, hour=8):
    scheduled_at = datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc)
    dose = DoseLog(
        medication_id=medication_id,
        schedule_time_id=None,
        scheduled_date=day,
        scheduled_at=scheduled_at,
        status=status_text,
    )
    db.add(dose)
    db.commit()


def get_today():
    return datetime.now(timezone.utc).date()


def test_history_returns_doses_newest_first(client):
    headers, user_id = register_and_login(client)
    today = get_today()

    db = get_test_db(client)
    medication = add_medication(db, user_id)
    add_dose(db, medication.id, today - timedelta(days=2), "taken")
    add_dose(db, medication.id, today - timedelta(days=1), "skipped")
    add_dose(db, medication.id, today, "pending")
    db.close()

    response = client.get("/history", headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["total"] == 3
    assert body["data"]["doses"][0]["status"] == "pending"
    assert body["data"]["doses"][2]["status"] == "taken"
    assert body["data"]["doses"][0]["medication_name"] == "Metformin"


def test_history_does_not_show_other_users_doses(client):
    headers_one, user_one_id = register_and_login(client, "one@example.com")
    headers_two, user_two_id = register_and_login(client, "two@example.com")

    db = get_test_db(client)
    medication = add_medication(db, user_one_id)
    add_dose(db, medication.id, get_today(), "taken")
    db.close()

    response = client.get("/history", headers=headers_two)

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 0


def test_history_can_filter_by_medication(client):
    headers, user_id = register_and_login(client)
    today = get_today()

    db = get_test_db(client)
    first_medication = add_medication(db, user_id, "Metformin")
    second_medication = add_medication(db, user_id, "Aspirin")
    add_dose(db, first_medication.id, today, "taken")
    add_dose(db, second_medication.id, today, "taken")
    second_id = second_medication.id
    db.close()

    response = client.get("/history?medication_id=" + str(second_id), headers=headers)
    body = response.json()

    assert body["data"]["total"] == 1
    assert body["data"]["doses"][0]["medication_name"] == "Aspirin"


def test_history_start_after_end_fails(client):
    headers, user_id = register_and_login(client)

    response = client.get(
        "/history?start_date=2026-11-10&end_date=2026-11-01", headers=headers
    )
    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["message"] == "Start date must not be after end date"


def test_history_range_too_long_fails(client):
    headers, user_id = register_and_login(client)

    response = client.get(
        "/history?start_date=2026-01-01&end_date=2026-11-01", headers=headers
    )
    body = response.json()

    assert response.status_code == 400
    assert body["message"] == "Date range cannot be more than 92 days"


def test_adherence_week_report(client):
    headers, user_id = register_and_login(client)
    today = get_today()

    db = get_test_db(client)
    medication = add_medication(db, user_id)
    add_dose(db, medication.id, today, "taken", 8)
    add_dose(db, medication.id, today, "taken", 14)
    add_dose(db, medication.id, today, "pending", 20)
    add_dose(db, medication.id, today, "pending", 22)
    add_dose(db, medication.id, today - timedelta(days=1), "taken", 8)
    add_dose(db, medication.id, today - timedelta(days=1), "skipped", 20)
    add_dose(db, medication.id, today - timedelta(days=3), "missed", 8)
    db.close()

    response = client.get("/reports/adherence?period=week", headers=headers)
    body = response.json()
    data = body["data"]

    assert response.status_code == 200
    assert body["success"] is True
    assert data["taken"] == 3
    assert data["skipped"] == 1
    assert data["missed"] == 1
    assert data["pending"] == 2
    assert data["total"] == 7
    assert data["adherence_percent"] == 60.0
    assert len(data["days"]) == 7
    assert data["days"][6]["total"] == 4


def test_adherence_with_no_doses_is_null(client):
    headers, user_id = register_and_login(client)

    response = client.get("/reports/adherence?period=month", headers=headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["total"] == 0
    assert data["adherence_percent"] is None
    assert len(data["days"]) == 30


def test_adherence_invalid_period_fails(client):
    headers, user_id = register_and_login(client)

    response = client.get("/reports/adherence?period=year", headers=headers)
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False


def test_reports_require_token(client):
    history_response = client.get("/history")
    report_response = client.get("/reports/adherence")

    assert history_response.status_code in (401, 403)
    assert report_response.status_code in (401, 403)