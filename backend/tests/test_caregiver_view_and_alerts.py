from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.database.connection import get_db
from app.main import app
from app.models.dose_log_model import DoseLog
from app.services import notification_service

CAREGIVERS_URL = "/caregivers"
INVITE_URL = "/caregivers/invite"
INVITATIONS_URL = "/caregivers/invitations"
PATIENTS_URL = "/caregivers/patients"
MEDICATIONS_URL = "/medications"
JOB_URL = "/internal/jobs/missed-doses"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
TEST_SECRET = "test-secret"


@pytest.fixture(autouse=True)
def set_job_settings(monkeypatch):
    # Fixed settings for these tests, not the values from .env
    monkeypatch.setattr(settings, "cron_secret", TEST_SECRET)
    monkeypatch.setattr(settings, "missed_dose_grace_minutes", 60)
    monkeypatch.setattr(settings, "fcm_enabled", False)


@pytest.fixture()
def push_calls(monkeypatch):
    # Replaces the real push function. It only remembers what would have been sent.
    calls = []

    def fake_send(db, user_id, title, body, data=None):
        call = {"user_id": user_id, "title": title, "body": body, "data": data}
        calls.append(call)
        return 1

    monkeypatch.setattr(notification_service, "send_push_to_user", fake_send)
    return calls


def get_missed_calls(push_calls):
    # Only the missed-dose pushes (invitation pushes are ignored)
    result = []
    for call in push_calls:
        if call["data"]["type"] == "missed_dose":
            result.append(call)
    return result


def get_invitation_calls(push_calls):
    result = []
    for call in push_calls:
        if call["data"]["type"] == "caregiver_invitation":
            result.append(call)
    return result


def get_headers_for(client, email, full_name="Test User"):
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": "test12345",
        "timezone": "Asia/Karachi",
    }
    client.post(REGISTER_URL, json=user_data)
    login_data = {"email": email, "password": "test12345"}
    response = client.post(LOGIN_URL, json=login_data)
    token = response.json()["data"]["access_token"]
    return {"Authorization": "Bearer " + token}


def get_patient_headers(client):
    return get_headers_for(client, "test@example.com", "Test User")


def get_caregiver_headers(client):
    return get_headers_for(client, "caregiver@example.com", "Care Giver")


def get_third_headers(client):
    return get_headers_for(client, "third@example.com", "Third Person")


def get_user_id(client, headers):
    response = client.get("/users/me", headers=headers)
    return response.json()["data"]["id"]


def invite(client, headers, email):
    return client.post(INVITE_URL, json={"email": email}, headers=headers)


def setup_accepted_link(client):
    # Creates a patient and a caregiver, sends the invitation and accepts it.
    # Returns both headers, the link id and the patient id.
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)

    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    accept_url = INVITATIONS_URL + "/" + str(link_id) + "/accept"
    client.put(accept_url, headers=caregiver_headers)

    patient_id = get_user_id(client, patient_headers)
    return patient_headers, caregiver_headers, link_id, patient_id


def make_permissions_body(view_medications=True, receive_alerts=True):
    body = {
        "can_view_medications": view_medications,
        "can_view_health": False,
        "receive_missed_alerts": receive_alerts,
    }
    return body


def set_permissions(client, patient_headers, link_id, body):
    url = CAREGIVERS_URL + "/" + str(link_id) + "/permissions"
    return client.put(url, json=body, headers=patient_headers)


def add_medication_with_schedule(client, headers, name="Alarm Med"):
    body = {
        "name": name,
        "dosage": "500 mg",
        "medication_type": "pill",
        "schedule": {
            "schedule_type": "daily",
            "times": [
                {"time_of_day": "08:00", "dose_amount": 1},
                {"time_of_day": "20:00", "dose_amount": 1},
            ],
        },
    }
    response = client.post(MEDICATIONS_URL + "/with-schedule", json=body, headers=headers)
    return response.json()["data"]["medication"]["id"]


def add_plain_medication(client, headers, name="Paracetamol"):
    body = {
        "name": name,
        "dosage": "500 mg",
        "medication_type": "pill",
        "start_date": "2026-11-01",
    }
    response = client.post(MEDICATIONS_URL, json=body, headers=headers)
    return response.json()["data"]["id"]


def insert_dose(medication_id, scheduled_at):
    # Puts a pending dose directly into the test database
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    dose = DoseLog(
        medication_id=medication_id,
        schedule_time_id=None,
        scheduled_date=scheduled_at.date(),
        scheduled_at=scheduled_at,
        status="pending",
    )
    db.add(dose)
    db.commit()

    db_generator.close()


def old_time():
    return datetime.now(timezone.utc) - timedelta(days=2)


def run_job(client):
    return client.post(JOB_URL, headers={"X-Cron-Secret": TEST_SECRET})


def today_url(patient_id):
    return PATIENTS_URL + "/" + str(patient_id) + "/today"


def medications_url(patient_id):
    return PATIENTS_URL + "/" + str(patient_id) + "/medications"


# ---------------- Caregiver views the patient's data ----------------


def test_caregiver_sees_patient_today(client):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    add_medication_with_schedule(client, patient_headers)

    response = client.get(today_url(patient_id), headers=caregiver_headers)
    body = response.json()
    data = body["data"]

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Patient's doses fetched successfully"
    assert data["timezone"] == "Asia/Karachi"
    assert data["total"] == 2
    assert data["pending"] == 2
    assert data["doses"][0]["medication_name"] == "Alarm Med"


def test_caregiver_sees_patient_medications(client):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    add_plain_medication(client, patient_headers, "Paracetamol")
    add_plain_medication(client, patient_headers, "Amoxicillin")

    response = client.get(medications_url(patient_id), headers=caregiver_headers)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Patient's medications fetched successfully"
    assert len(body["data"]) == 2
    assert body["data"][0]["name"] == "Amoxicillin"


def test_deleted_medication_is_not_shown_to_the_caregiver(client):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    medication_id = add_plain_medication(client, patient_headers)
    client.delete(MEDICATIONS_URL + "/" + str(medication_id), headers=patient_headers)

    response = client.get(medications_url(patient_id), headers=caregiver_headers)

    assert response.status_code == 200
    assert len(response.json()["data"]) == 0


def test_without_permission_the_caregiver_sees_nothing(client):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    add_medication_with_schedule(client, patient_headers)
    set_permissions(
        client, patient_headers, link_id, make_permissions_body(view_medications=False)
    )

    today = client.get(today_url(patient_id), headers=caregiver_headers)
    medications = client.get(medications_url(patient_id), headers=caregiver_headers)

    assert today.status_code == 404
    assert today.json()["message"] == "Patient not found"
    assert medications.status_code == 404
    assert medications.json()["message"] == "Patient not found"


def test_pending_caregiver_cannot_view(client):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    invite(client, patient_headers, "caregiver@example.com")
    patient_id = get_user_id(client, patient_headers)
    add_medication_with_schedule(client, patient_headers)

    today = client.get(today_url(patient_id), headers=caregiver_headers)
    medications = client.get(medications_url(patient_id), headers=caregiver_headers)

    assert today.status_code == 404
    assert medications.status_code == 404


def test_stranger_cannot_view(client):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    add_medication_with_schedule(client, patient_headers)
    third_headers = get_third_headers(client)

    today = client.get(today_url(patient_id), headers=third_headers)
    medications = client.get(medications_url(patient_id), headers=third_headers)

    assert today.status_code == 404
    assert medications.status_code == 404


def test_removed_caregiver_cannot_view(client):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    add_medication_with_schedule(client, patient_headers)
    client.delete(CAREGIVERS_URL + "/" + str(link_id), headers=patient_headers)

    today = client.get(today_url(patient_id), headers=caregiver_headers)

    assert today.status_code == 404
    assert today.json()["message"] == "Patient not found"


def test_viewing_patient_data_requires_a_token(client):
    response = client.get(today_url(1))

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)


# ---------------- Missed-dose alerts to caregivers ----------------


def test_caregiver_gets_an_alert_for_a_missed_dose(client, push_calls):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    caregiver_id = get_user_id(client, caregiver_headers)
    medication_id = add_plain_medication(client, patient_headers, "Paracetamol")
    insert_dose(medication_id, old_time())

    response = run_job(client)
    data = response.json()["data"]
    missed_calls = get_missed_calls(push_calls)

    assert response.status_code == 200
    assert data["missed_count"] == 1
    assert data["alerts_sent"] == 1
    assert len(missed_calls) == 1
    assert missed_calls[0]["user_id"] == caregiver_id
    assert missed_calls[0]["title"] == "Missed dose"
    assert "Test User" in missed_calls[0]["body"]
    assert "Paracetamol" in missed_calls[0]["body"]
    assert missed_calls[0]["data"]["patient_id"] == patient_id


def test_no_alert_when_the_caregiver_turned_alerts_off(client, push_calls):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    set_permissions(
        client, patient_headers, link_id, make_permissions_body(receive_alerts=False)
    )
    medication_id = add_plain_medication(client, patient_headers)
    insert_dose(medication_id, old_time())

    response = run_job(client)

    # The dose is still marked as missed, only the alert is skipped
    assert response.json()["data"]["missed_count"] == 1
    assert response.json()["data"]["alerts_sent"] == 0
    assert len(get_missed_calls(push_calls)) == 0


def test_no_alert_for_a_pending_caregiver(client, push_calls):
    patient_headers = get_patient_headers(client)
    get_caregiver_headers(client)
    invite(client, patient_headers, "caregiver@example.com")
    medication_id = add_plain_medication(client, patient_headers)
    insert_dose(medication_id, old_time())

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 1
    assert len(get_missed_calls(push_calls)) == 0


def test_many_missed_doses_send_one_alert(client, push_calls):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    medication_id = add_plain_medication(client, patient_headers)
    insert_dose(medication_id, old_time())
    insert_dose(medication_id, old_time() - timedelta(days=1))

    response = run_job(client)
    missed_calls = get_missed_calls(push_calls)

    assert response.json()["data"]["missed_count"] == 2
    assert len(missed_calls) == 1
    assert "2 doses" in missed_calls[0]["body"]


def test_no_alert_when_nothing_is_missed(client, push_calls):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    add_plain_medication(client, patient_headers)

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 0
    assert len(get_missed_calls(push_calls)) == 0


def test_caregiver_is_not_alerted_for_another_patient(client, push_calls):
    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)

    # A third person (not a patient of this caregiver) misses a dose
    third_headers = get_third_headers(client)
    medication_id = add_plain_medication(client, third_headers)
    insert_dose(medication_id, old_time())

    response = run_job(client)

    assert response.json()["data"]["missed_count"] == 1
    assert len(get_missed_calls(push_calls)) == 0


def test_a_push_error_does_not_break_the_job(client, monkeypatch):
    def broken_send(db, user_id, title, body, data=None):
        raise RuntimeError("push failed")

    monkeypatch.setattr(notification_service, "send_push_to_user", broken_send)

    patient_headers, caregiver_headers, link_id, patient_id = setup_accepted_link(client)
    medication_id = add_plain_medication(client, patient_headers)
    insert_dose(medication_id, old_time())

    response = run_job(client)

    assert response.status_code == 200
    assert response.json()["data"]["missed_count"] == 1
    assert response.json()["data"]["alerts_sent"] == 0


# ---------------- Invitation push ----------------


def test_invitation_sends_a_push_when_the_person_has_an_account(client, push_calls):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    caregiver_id = get_user_id(client, caregiver_headers)

    response = invite(client, patient_headers, "caregiver@example.com")
    invitation_calls = get_invitation_calls(push_calls)

    assert response.status_code == 201
    assert len(invitation_calls) == 1
    assert invitation_calls[0]["user_id"] == caregiver_id
    assert invitation_calls[0]["title"] == "Caregiver invitation"
    assert "Test User" in invitation_calls[0]["body"]


def test_invitation_sends_no_push_when_there_is_no_account(client, push_calls):
    patient_headers = get_patient_headers(client)

    response = invite(client, patient_headers, "noaccount@example.com")

    assert response.status_code == 201
    assert len(get_invitation_calls(push_calls)) == 0


def test_a_push_error_does_not_break_the_invitation(client, monkeypatch):
    def broken_send(db, user_id, title, body, data=None):
        raise RuntimeError("push failed")

    monkeypatch.setattr(notification_service, "send_push_to_user", broken_send)

    patient_headers = get_patient_headers(client)
    get_caregiver_headers(client)

    response = invite(client, patient_headers, "caregiver@example.com")

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "pending"