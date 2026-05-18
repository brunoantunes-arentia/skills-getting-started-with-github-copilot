import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy

@pytest.fixture(autouse=True)
def reset_activities():
    # Deep copy the original activities state before each test
    orig = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(orig))

@pytest.fixture
def client():
    return TestClient(app)

# --- GET / (root) ---
def test_root_redirects_to_static_index(client):
    # Arrange
    # ...nothing to arrange...
    # Act
    response = client.get("/")
    # Assert
    # Accept either a direct 200 (TestClient follows redirects by default) or a redirect status
    if response.status_code in (307, 302):
        assert response.headers["location"].endswith("/static/index.html")
    elif response.status_code == 200:
        # If not a redirect, check that the final URL is the static index
        # TestClient follows redirects by default, so this is valid
        assert b"Mergington High School" in response.content
    else:
        pytest.fail(f"Unexpected status code: {response.status_code}")

# --- GET /activities ---
def test_get_activities_returns_all(client):
    # Arrange
    # ...nothing to arrange...
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    for act in data.values():
        assert "description" in act
        assert "schedule" in act
        assert "max_participants" in act
        assert "participants" in act

# --- POST /activities/{activity_name}/signup ---
def test_signup_success(client):
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    assert email not in activities[activity]["participants"]
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    # Assert
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert "Signed up" in response.json()["message"]

def test_signup_activity_not_found(client):
    # Arrange
    activity = "Nonexistent Club"
    email = "someone@mergington.edu"
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

def test_signup_duplicate(client):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"

# --- DELETE /activities/{activity_name}/unregister ---
def test_unregister_success(client):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    # Assert
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]
    assert "Unregistered" in response.json()["message"]

def test_unregister_activity_not_found(client):
    # Arrange
    activity = "Nonexistent Club"
    email = "someone@mergington.edu"
    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

def test_unregister_not_signed_up(client):
    # Arrange
    activity = "Chess Club"
    email = "notregistered@mergington.edu"
    assert email not in activities[activity]["participants"]
    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
