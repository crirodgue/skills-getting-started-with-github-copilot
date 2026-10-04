import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_SIGNUP_PATH = "/activities/Chess%20Club/signup"


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Test activity",
            "schedule": "Mondays at 3 PM",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "Chess Club": {
            "description": "Test activity",
            "schedule": "Mondays at 3 PM",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        }
    }


def test_signup_adds_participant(client):
    response = client.post(
        ACTIVITY_SIGNUP_PATH,
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@example.com for Chess Club"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "existing@example.com",
        "new@example.com",
    ]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        ACTIVITY_SIGNUP_PATH,
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "existing@example.com"
    ]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    response = client.delete(
        ACTIVITY_SIGNUP_PATH,
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.com from Chess Club"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == []


def test_unregister_rejects_participant_not_signed_up(client):
    response = client.delete(
        ACTIVITY_SIGNUP_PATH,
        params={"email": "missing@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}