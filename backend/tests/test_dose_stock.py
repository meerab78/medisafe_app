from datetime import date, datetime, time, timezone

from app.database.connection import get_db
from app.models.dose_log_model import DoseLog
from app.models.medication_model import Medication
from app.models.schedule_model import Schedule, ScheduleTime


def get_test_db(client):
    override_function = client.app.dependency_overrides[get_db]
    db_generator = override_function()
    return next(db_generator)


def register_and_login(client):
    user_data = {
        "full_name": "Stock User",
        "email": "stock@example.com",
        "password": "test12345",
        "timezone": "UTC",
    }
    client.post("/auth/register", json=user_data)
    login_data = {"email": "stock@example.com", "password": "test12345"}
    login_response = client.post("/auth/login", json=login_data)
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    profile_response = client.get("/users/me", headers=headers)
    user_id = profile_response.json()["data"]["id"]
    return headers, user_id


def create_dose(
    db, user_id, stock=10, dose_amount=2, status_text="pending", with_schedule_time=True
):
    medication = Medication(
        user_id=user_id,
        name="Stock Test",
        dosage="500 mg",
        medication_type="tablet",
        start_date=date(2026, 1, 1),
        stock_quantity=stock,
        low_stock_threshold=5,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    schedule_time_id = None
    if with_schedule_time:
        schedule = Schedule(medication_id=medication.id, schedule_type="daily")
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        schedule_time = ScheduleTime(
            schedule_id=schedule.id,
            time_of_day=time(8, 0),
            dose_amount=dose_amount,
        )
        db.add(schedule_time)
        db.commit()
        db.refresh(schedule_time)
        schedule_time_id = schedule_time.id

    today = datetime.now(timezone.utc).date()
    scheduled_at = datetime(today.year, today.month, today.day, 8, 0, tzinfo=timezone.utc)
    dose = DoseLog(
        medication_id=medication.id,
        schedule_time_id=schedule_time_id,
        scheduled_date=today,
        scheduled_at=scheduled_at,
        status=status_text,
    )
    db.add(dose)
    db.commit()
    db.refresh(dose)
    return medication.id, dose.id


def get_stock(client, medication_id):
    db = get_test_db(client)
    medication = db.get(Medication, medication_id)
    stock = medication.stock_quantity
    db.close()
    return stock


def prepare(client, **options):
    headers, user_id = register_and_login(client)
    db = get_test_db(client)
    medication_id, dose_id = create_dose(db, user_id, **options)
    db.close()
    return headers, medication_id, dose_id


def test_taking_a_dose_reduces_stock_by_dose_amount(client):
    headers, medication_id, dose_id = prepare(client, stock=10, dose_amount=2)

    response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)

    assert response.status_code == 200
    assert get_stock(client, medication_id) == 8


def test_skipping_a_dose_does_not_change_stock(client):
    headers, medication_id, dose_id = prepare(client, stock=10, dose_amount=2)

    response = client.put("/doses/" + str(dose_id) + "/skip", headers=headers)

    assert response.status_code == 200
    assert get_stock(client, medication_id) == 10


def test_stock_never_goes_below_zero(client):
    headers, medication_id, dose_id = prepare(client, stock=1, dose_amount=2)

    response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)

    assert response.status_code == 200
    assert get_stock(client, medication_id) == 0


def test_dose_without_schedule_time_uses_one_tablet(client):
    headers, medication_id, dose_id = prepare(
        client, stock=10, with_schedule_time=False
    )

    response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)

    assert response.status_code == 200
    assert get_stock(client, medication_id) == 9


def test_late_taking_of_a_missed_dose_reduces_stock(client):
    headers, medication_id, dose_id = prepare(
        client, stock=10, dose_amount=1, status_text="missed"
    )

    response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)

    assert response.status_code == 200
    assert get_stock(client, medication_id) == 9


def test_taking_the_same_dose_twice_reduces_stock_only_once(client):
    headers, medication_id, dose_id = prepare(client, stock=10, dose_amount=2)

    first_response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)
    second_response = client.put("/doses/" + str(dose_id) + "/take", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert get_stock(client, medication_id) == 8