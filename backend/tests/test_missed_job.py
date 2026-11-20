from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.database.connection import get_db
from app.main import app
from app.models.dose_log_model import DoseLog

JOB_URL = "/internal/jobs/missed-doses"
MEDICATIONS_URL = "/medications"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
TEST_SECRET = "test-secret"


@pytest.fixture(autouse=True)
def set_job_settings(monkeypatch):
    # Use fixed settings in these tests, not the values from .env
    monkeypatch.setattr(settings, "cron_secret", TEST_SECRET)
    monkeypatch.setattr(settings, "missed_dose_grace_minutes", 60)


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


def add_medication(client, headers):
    body = {
        "name": "Paracetamol",
        "dosage": "500 mg",
        "medication_type": "tablet",
        "start_date": "2026-11-01",
    }
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)
    return response.json()["data"]["id"]


def insert_dose(medication_id, scheduled_at, status="pending"):
    # Uses the same test database that the client uses
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    dose = DoseLog(
        medication_id=medication_id,
        schedule_time_id=None,
        scheduled_date=scheduled_at.date(),
        scheduled_at=scheduled_at,
        status=status,
    )
    db.add(dose)
    db.commit()
    db.refresh(dose)
    dose_id = dose.id

    db_generator.close()
    return dose_id


def get_dose_status(dose_id):
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    dose = db.get(DoseLog, dose_id)
    status = dose.status

    db_generator.close()
    return status


def run_job(client, secret=TEST_SECRET):
    return client.post(JOB_URL, headers={"X-Cron-Secret": secret})


def now_utc():
    return datetime.now(timezone.utc)


# ---------------- Secret protection ----------------


def test_job_without_secret_header_fails(client):
    response = client.post(JOB_URL)
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["message"] == "Unauthorized"


def test_job_with_wrong_secret_fails(client):
    response = run_job(client, secret="wrong-secret")

    assert response.status_code == 401
    assert response.json()["message"] == "Unauthorized"


def test_job_is_locked_when_secret_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "cron_secret", "")

    response = client.post(JOB_URL, headers={"X-Cron-Secret": ""})

    assert response.status_code == 401


# ---------------- Marking doses as missed ----------------


def test_overdue_pending_dose_becomes_missed(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    dose_id = insert_dose(medication_id, now_utc() - timedelta(days=2))

    response = run_job(client)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Missed dose check completed"
    assert body["data"]["missed_count"] == 1
    assert get_dose_status(dose_id) == "missed"


def test_dose_inside_grace_time_stays_pending(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    # Only 10 minutes late, the grace time is 60 minutes
    dose_id = insert_dose(medication_id, now_utc() - timedelta(minutes=10))

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 0
    assert get_dose_status(dose_id) == "pending"


def test_future_dose_stays_pending(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    dose_id = insert_dose(medication_id, now_utc() + timedelta(days=1))

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 0
    assert get_dose_status(dose_id) == "pending"


def test_taken_dose_is_not_changed(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    dose_id = insert_dose(
        medication_id, now_utc() - timedelta(days=2), status="taken"
    )

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 0
    assert get_dose_status(dose_id) == "taken"


def test_inactive_medication_dose_is_not_changed(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    dose_id = insert_dose(medication_id, now_utc() - timedelta(days=2))

    # Soft delete the medication
    client.delete(MEDICATIONS_URL + "/" + str(medication_id), headers=headers)

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 0
    assert get_dose_status(dose_id) == "pending"


def test_running_job_twice_marks_only_once(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    insert_dose(medication_id, now_utc() - timedelta(days=2))

    first = run_job(client)
    second = run_job(client)

    assert first.json()["data"]["missed_count"] == 1
    assert second.json()["data"]["missed_count"] == 0


def test_missed_dose_can_still_be_taken_late(client):
    headers = get_auth_headers(client)
    medication_id = add_medication(client, headers)
    dose_id = insert_dose(medication_id, now_utc() - timedelta(days=2))
    run_job(client)

    response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["status"] == "taken"
    assert body["data"]["taken_at"] is not None