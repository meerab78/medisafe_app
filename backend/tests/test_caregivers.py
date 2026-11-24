CAREGIVERS_URL = "/caregivers"
INVITE_URL = "/caregivers/invite"
INVITATIONS_URL = "/caregivers/invitations"
PATIENTS_URL = "/caregivers/patients"
REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"


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


def invite(client, headers, email):
    body = {"email": email}
    return client.post(INVITE_URL, json=body, headers=headers)


def get_list(client, url, headers):
    response = client.get(url, headers=headers)
    return response.json()["data"]


def make_permissions_body():
    body = {
        "can_view_medications": False,
        "can_view_health": True,
        "receive_missed_alerts": False,
    }
    return body


def setup_accepted_link(client):
    # Creates a patient, a caregiver, sends the invitation and accepts it.
    # Returns the headers of both users and the link id.
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)

    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    accept_url = INVITATIONS_URL + "/" + str(link_id) + "/accept"
    client.put(accept_url, headers=caregiver_headers)

    return patient_headers, caregiver_headers, link_id


# ---------------- Invite ----------------


def test_invite_success_for_email_without_account(client):
    headers = get_patient_headers(client)
    response = invite(client, headers, "new@example.com")
    body = response.json()
    data = body["data"]

    assert response.status_code == 201
    assert body["success"] is True
    assert body["message"] == "Invitation sent successfully"
    assert data["email"] == "new@example.com"
    assert data["status"] == "pending"
    assert data["caregiver_name"] is None
    assert data["can_view_medications"] is True
    assert data["can_view_health"] is False
    assert data["receive_missed_alerts"] is True


def test_invite_email_is_lower_cased_and_shows_name(client):
    headers = get_patient_headers(client)
    get_caregiver_headers(client)

    response = invite(client, headers, "Caregiver@Example.com")
    data = response.json()["data"]

    assert response.status_code == 201
    assert data["email"] == "caregiver@example.com"
    assert data["caregiver_name"] == "Care Giver"


def test_cannot_invite_yourself(client):
    headers = get_patient_headers(client)
    response = invite(client, headers, "TEST@example.com")
    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["message"] == "You cannot invite yourself"


def test_duplicate_pending_invite_fails(client):
    headers = get_patient_headers(client)
    invite(client, headers, "new@example.com")
    response = invite(client, headers, "new@example.com")

    assert response.status_code == 409
    assert response.json()["message"] == "You have already invited this person"


def test_invalid_email_fails(client):
    headers = get_patient_headers(client)
    response = invite(client, headers, "not-an-email")
    body = response.json()

    assert response.status_code == 422
    assert body["message"] == "Invalid input data"
    assert body["errors"][0]["field"] == "email"


def test_at_most_five_caregivers(client):
    headers = get_patient_headers(client)

    for number in range(5):
        email = "person" + str(number) + "@example.com"
        response = invite(client, headers, email)
        assert response.status_code == 201

    response = invite(client, headers, "person5@example.com")

    assert response.status_code == 400
    assert response.json()["message"] == "You can have at most 5 caregivers"


def test_invite_after_accept_fails(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)
    response = invite(client, patient_headers, "caregiver@example.com")

    assert response.status_code == 409
    assert response.json()["message"] == "This person is already your caregiver"


# ---------------- Patient list ----------------


def test_patient_sees_my_caregivers(client):
    headers = get_patient_headers(client)
    invite(client, headers, "one@example.com")
    invite(client, headers, "two@example.com")

    response = client.get(CAREGIVERS_URL, headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Caregivers fetched successfully"
    assert len(response.json()["data"]) == 2


# ---------------- Invitations ----------------


def test_invited_person_sees_the_invitation(client):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    response = client.get(INVITATIONS_URL, headers=caregiver_headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["id"] == link_id
    assert data[0]["patient_name"] == "Test User"
    assert data[0]["patient_email"] == "test@example.com"


def test_other_person_does_not_see_the_invitation(client):
    patient_headers = get_patient_headers(client)
    get_caregiver_headers(client)
    third_headers = get_third_headers(client)
    invite(client, patient_headers, "caregiver@example.com")

    invitations = get_list(client, INVITATIONS_URL, third_headers)

    assert len(invitations) == 0


def test_accept_invitation(client):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    accept_url = INVITATIONS_URL + "/" + str(link_id) + "/accept"
    response = client.put(accept_url, headers=caregiver_headers)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Invitation accepted"
    assert body["data"]["status"] == "accepted"
    assert body["data"]["patient_name"] == "Test User"

    # The patient sees it as accepted
    caregivers = get_list(client, CAREGIVERS_URL, patient_headers)
    assert caregivers[0]["status"] == "accepted"

    # The caregiver sees the patient, and the invitation is gone
    patients = get_list(client, PATIENTS_URL, caregiver_headers)
    assert len(patients) == 1
    assert patients[0]["patient_name"] == "Test User"
    assert len(get_list(client, INVITATIONS_URL, caregiver_headers)) == 0


def test_accept_twice_fails(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)

    accept_url = INVITATIONS_URL + "/" + str(link_id) + "/accept"
    response = client.put(accept_url, headers=caregiver_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Invitation not found"


def test_cannot_accept_someone_elses_invitation(client):
    patient_headers = get_patient_headers(client)
    get_caregiver_headers(client)
    third_headers = get_third_headers(client)
    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    accept_url = INVITATIONS_URL + "/" + str(link_id) + "/accept"
    response = client.put(accept_url, headers=third_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Invitation not found"

    # The invitation must still be pending for the patient
    caregivers = get_list(client, CAREGIVERS_URL, patient_headers)
    assert caregivers[0]["status"] == "pending"


def test_reject_invitation(client):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    reject_url = INVITATIONS_URL + "/" + str(link_id) + "/reject"
    response = client.put(reject_url, headers=caregiver_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Invitation rejected"
    assert len(get_list(client, CAREGIVERS_URL, patient_headers)) == 0
    assert len(get_list(client, INVITATIONS_URL, caregiver_headers)) == 0
    assert len(get_list(client, PATIENTS_URL, caregiver_headers)) == 0


def test_invite_again_after_reject(client):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]
    reject_url = INVITATIONS_URL + "/" + str(link_id) + "/reject"
    client.put(reject_url, headers=caregiver_headers)

    response = invite(client, patient_headers, "caregiver@example.com")

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "pending"
    assert len(get_list(client, INVITATIONS_URL, caregiver_headers)) == 1


# ---------------- Permissions ----------------


def test_patient_can_update_permissions(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)

    url = CAREGIVERS_URL + "/" + str(link_id) + "/permissions"
    response = client.put(url, json=make_permissions_body(), headers=patient_headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert response.json()["message"] == "Permissions updated successfully"
    assert data["can_view_medications"] is False
    assert data["can_view_health"] is True
    assert data["receive_missed_alerts"] is False

    # The caregiver sees the new permissions too
    patients = get_list(client, PATIENTS_URL, caregiver_headers)
    assert patients[0]["can_view_health"] is True
    assert patients[0]["can_view_medications"] is False


def test_caregiver_cannot_change_permissions(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)

    url = CAREGIVERS_URL + "/" + str(link_id) + "/permissions"
    response = client.put(url, json=make_permissions_body(), headers=caregiver_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Caregiver not found"


# ---------------- Remove and leave ----------------


def test_patient_can_remove_caregiver(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)

    response = client.delete(CAREGIVERS_URL + "/" + str(link_id), headers=patient_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Caregiver removed successfully"
    assert len(get_list(client, CAREGIVERS_URL, patient_headers)) == 0
    assert len(get_list(client, PATIENTS_URL, caregiver_headers)) == 0


def test_other_user_cannot_remove_caregiver(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)
    third_headers = get_third_headers(client)

    response = client.delete(CAREGIVERS_URL + "/" + str(link_id), headers=third_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Caregiver not found"
    assert len(get_list(client, CAREGIVERS_URL, patient_headers)) == 1


def test_caregiver_can_leave(client):
    patient_headers, caregiver_headers, link_id = setup_accepted_link(client)

    url = PATIENTS_URL + "/" + str(link_id)
    response = client.delete(url, headers=caregiver_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "You are no longer a caregiver for this person"
    assert len(get_list(client, PATIENTS_URL, caregiver_headers)) == 0
    assert len(get_list(client, CAREGIVERS_URL, patient_headers)) == 0


def test_cannot_leave_a_pending_invitation(client):
    patient_headers = get_patient_headers(client)
    caregiver_headers = get_caregiver_headers(client)
    created = invite(client, patient_headers, "caregiver@example.com")
    link_id = created.json()["data"]["id"]

    url = PATIENTS_URL + "/" + str(link_id)
    response = client.delete(url, headers=caregiver_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Patient not found"


def test_caregivers_without_token_fail(client):
    response = client.get(CAREGIVERS_URL)

    # Depending on the FastAPI version this is 401 or 403
    assert response.status_code in (401, 403)