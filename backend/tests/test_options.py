from app.schemas.medication_schema import MedicationCreate

WIZARD_URL = "/options/medication-wizard"
MEDICATIONS_URL = "/medications"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


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


def get_steps(client):
    response = client.get(WIZARD_URL)
    return response.json()["data"]["steps"]


def find_step(steps, step_id):
    for step in steps:
        if step["id"] == step_id:
            return step
    return None


def get_values(step):
    values = []
    for option in step["options"]:
        values.append(option["value"])
    return values


def make_body():
    # Returns a fresh dictionary each time
    body = {
        "name": "Wizard Test",
        "dosage": "1 unit",
        "medication_type": "pill",
        "start_date": "2026-11-21",
    }
    return body


def test_wizard_is_public_and_returns_steps(client):
    # No token is sent on purpose
    response = client.get(WIZARD_URL)
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["message"] == "Medication wizard fetched successfully"
    assert body["data"]["version"] == 1
    assert len(body["data"]["steps"]) > 0


def test_steps_come_in_the_expected_order(client):
    steps = get_steps(client)

    ids = []
    for step in steps:
        ids.append(step["id"])

    expected = [
        "name",
        "form",
        "route",
        "dosage",
        "reason",
        "frequency",
        "days",
        "times_per_day",
        "hours_between",
        "first_dose_time",
        "times",
        "start_date",
        "duration",
        "end_date",
        "stock_quantity",
        "low_stock_threshold",
        "icon",
        "food_instruction",
        "instructions",
    ]
    assert ids == expected


def test_form_options_are_the_seven_forms(client):
    steps = get_steps(client)
    form_step = find_step(steps, "form")

    assert form_step["type"] == "single_choice"
    assert form_step["field"] == "medication_type"
    assert get_values(form_step) == [
        "pill",
        "injection",
        "liquid",
        "drops",
        "inhaler",
        "powder",
        "other",
    ]


def test_route_step_is_shown_only_for_other(client):
    steps = get_steps(client)
    route_step = find_step(steps, "route")

    assert route_step["show_when"]["step"] == "form"
    assert route_step["show_when"]["equals"] == "other"
    assert get_values(route_step) == [
        "mouth",
        "nose",
        "ears",
        "injection",
        "vaginal",
        "inhaled",
    ]


def test_frequency_options_and_interval_extra(client):
    steps = get_steps(client)
    frequency_step = find_step(steps, "frequency")

    assert get_values(frequency_step) == ["daily", "interval", "weekly"]

    interval_option = frequency_step["options"][1]
    assert interval_option["label"] == "Every other day"
    assert interval_option["extra"] == {"schedule.interval_days": 2}


def test_days_step_has_seven_days_for_weekly_only(client):
    steps = get_steps(client)
    days_step = find_step(steps, "days")

    assert days_step["type"] == "multi_choice"
    assert get_values(days_step) == [0, 1, 2, 3, 4, 5, 6]
    assert days_step["show_when"]["step"] == "frequency"
    assert days_step["show_when"]["equals"] == "weekly"


def test_hourly_steps_and_times_step_use_the_same_answer(client):
    steps = get_steps(client)
    hours_step = find_step(steps, "hours_between")
    times_step = find_step(steps, "times")

    assert hours_step["show_when"]["equals"] == "hourly"
    assert times_step["show_when"]["not_equals"] == "hourly"
    assert times_step["count_from"] == "times_per_day"


def test_optional_steps_can_be_skipped(client):
    steps = get_steps(client)

    assert find_step(steps, "name")["required"] is True
    assert find_step(steps, "reason")["required"] is False
    assert find_step(steps, "icon")["required"] is False
    assert find_step(steps, "instructions")["required"] is False


def test_extras_section_starts_at_start_date(client):
    steps = get_steps(client)

    extras_ids = []
    main_ids = []
    for step in steps:
        if step["section"] == "extras":
            extras_ids.append(step["id"])
        else:
            main_ids.append(step["id"])

    assert main_ids[-1] == "times"
    assert extras_ids[0] == "start_date"
    assert extras_ids[-1] == "instructions"


def test_show_when_points_to_an_earlier_step(client):
    steps = get_steps(client)

    seen_ids = []
    for step in steps:
        if step["show_when"] is not None:
            assert step["show_when"]["step"] in seen_ids
        seen_ids.append(step["id"])


def test_plain_fields_exist_in_the_medication_schema(client):
    steps = get_steps(client)

    for step in steps:
        field = step["field"]
        if field is None:
            continue
        # Fields like "schedule.times" belong to the schedule, not the medication
        if "." in field:
            continue
        assert field in MedicationCreate.model_fields


def test_every_form_option_is_accepted_by_the_server(client):
    headers = get_auth_headers(client)
    steps = get_steps(client)
    form_step = find_step(steps, "form")

    for value in get_values(form_step):
        body = make_body()
        body["medication_type"] = value
        if value == "other":
            body["route"] = "mouth"
        response = client.post(MEDICATIONS_URL, json=body, headers=headers)
        assert response.status_code == 201


def test_every_route_option_is_accepted_by_the_server(client):
    headers = get_auth_headers(client)
    steps = get_steps(client)
    route_step = find_step(steps, "route")

    for value in get_values(route_step):
        body = make_body()
        body["medication_type"] = "other"
        body["route"] = value
        response = client.post(MEDICATIONS_URL, json=body, headers=headers)
        assert response.status_code == 201


def test_every_food_and_icon_option_is_accepted_by_the_server(client):
    headers = get_auth_headers(client)
    steps = get_steps(client)
    food_step = find_step(steps, "food_instruction")
    icon_step = find_step(steps, "icon")

    for value in get_values(food_step):
        body = make_body()
        body["food_instruction"] = value
        response = client.post(MEDICATIONS_URL, json=body, headers=headers)
        assert response.status_code == 201

    for value in get_values(icon_step):
        body = make_body()
        body["icon"] = value
        response = client.post(MEDICATIONS_URL, json=body, headers=headers)
        assert response.status_code == 201