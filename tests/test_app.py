from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as api


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "activities", deepcopy(api.activities))
    return TestClient(api.app)


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert set(activities) == {"Chess Club", "Programming Class", "Gym Class"}
    assert activities["Chess Club"] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }


def test_signup_adds_participant_and_returns_confirmation(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Chess Club"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
        "student@mergington.edu",
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_allows_duplicate_email(client):
    email = "student@mergington.edu"

    first_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )
    second_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert client.get("/activities").json()["Chess Club"]["participants"].count(email) == 2


def test_signup_is_allowed_when_activity_is_at_capacity(client):
    activity = api.activities["Chess Club"]
    participants = activity["participants"]
    capacity = activity["max_participants"]
    participants.extend(
        f"student{index}@mergington.edu"
        for index in range(capacity - len(participants))
    )

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "additional@mergington.edu"},
    )

    assert response.status_code == 200
    updated_activity = client.get("/activities").json()["Chess Club"]
    assert len(updated_activity["participants"]) == capacity + 1
