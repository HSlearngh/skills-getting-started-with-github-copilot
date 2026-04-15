"""
API tests using AAA (Arrange-Act-Assert) pattern for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 2,  # Low capacity for testing
            "participants": ["emma@mergington.edu"]
        },
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


# ==================== GET /activities Tests ====================

class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """ARRANGE: Setup (implicit via fixture)
           ACT: Make GET request to /activities
           ASSERT: Response contains all activities with correct structure"""
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 2

    def test_get_activities_returns_correct_activity_structure(self, client):
        """ARRANGE: Setup (implicit via fixture)
           ACT: Get activities
           ASSERT: Each activity has required fields"""
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_shows_current_participants(self, client):
        """ARRANGE: Setup (implicit via fixture with participants)
           ACT: Get activities
           ASSERT: Participants list matches initial state"""
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


# ==================== POST /signup Tests ====================

class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful_for_available_spot(self, client):
        """ARRANGE: Activity has available spots
           ACT: Sign up new student
           ASSERT: Student is added and message returned"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_fails_for_nonexistent_activity(self, client):
        """ARRANGE: Activity does not exist
           ACT: Attempt signup
           ASSERT: 404 error returned"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_fails_for_already_enrolled_student(self, client):
        """ARRANGE: Student is already enrolled
           ACT: Attempt to sign up for same activity
           ASSERT: 400 error returned"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already enrolled

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_fails_when_activity_at_max_capacity(self, client):
        """ARRANGE: Activity is at max capacity
           ACT: Attempt to sign up
           ASSERT: 400 error returned"""
        # Arrange
        activity_name = "Programming Class"
        # Already has 1 participant, max is 2, so add one more to reach capacity
        activities[activity_name]["participants"].append("second@mergington.edu")
        email = "third@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "at max capacity" in response.json()["detail"]

    def test_signup_updates_participant_count(self, client):
        """ARRANGE: Get initial participant count
           ACT: Add new participant
           ASSERT: Count increases by 1"""
        # Arrange
        activity_name = "Chess Club"
        initial_count = len(activities[activity_name]["participants"])
        email = "newstudent@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        new_count = len(activities[activity_name]["participants"])
        assert new_count == initial_count + 1


# ==================== DELETE /signup Tests ====================

class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_successful_for_enrolled_student(self, client):
        """ARRANGE: Student is enrolled
           ACT: Delete signup
           ASSERT: Student is removed and message returned"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_unregister_fails_for_nonexistent_activity(self, client):
        """ARRANGE: Activity does not exist
           ACT: Attempt unregister
           ASSERT: 404 error returned"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_fails_for_not_enrolled_student(self, client):
        """ARRANGE: Student is not enrolled
           ACT: Attempt unregister
           ASSERT: 400 error returned"""
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_updates_participant_count(self, client):
        """ARRANGE: Get initial participant count
           ACT: Remove participant
           ASSERT: Count decreases by 1"""
        # Arrange
        activity_name = "Chess Club"
        initial_count = len(activities[activity_name]["participants"])
        email = "michael@mergington.edu"

        # Act
        client.delete(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert
        new_count = len(activities[activity_name]["participants"])
        assert new_count == initial_count - 1

    def test_unregister_allows_new_signup_in_full_activity(self, client):
        """ARRANGE: Activity at capacity after signup
           ACT: Unregister one student, then sign up different student
           ASSERT: New signup succeeds"""
        # Arrange
        activity_name = "Programming Class"
        # Fill to capacity
        activities[activity_name]["participants"] = ["emma@mergington.edu", "full@mergington.edu"]
        new_email = "waitlisted@mergington.edu"

        # Act - Unregister to free spot
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": "full@mergington.edu"}
        )
        # Try to sign up new student
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        assert new_email in activities[activity_name]["participants"]


# ==================== Integration Tests ====================

class TestActivityWorkflow:
    """Integration tests for complete workflows"""

    def test_complete_signup_and_unregister_workflow(self, client):
        """ARRANGE: Empty activity setup
           ACT: Sign up, verify in list, unregister, verify removed
           ASSERT: All operations succeed"""
        # Arrange
        activity_name = "Chess Club"
        email = "workflow@mergington.edu"

        # Act & Assert - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Act & Assert - Verify in list
        get_response = client.get("/activities")
        assert email in get_response.json()[activity_name]["participants"]

        # Act & Assert - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Act & Assert - Verify removed
        get_response = client.get("/activities")
        assert email not in get_response.json()[activity_name]["participants"]

    def test_multiple_students_signup_and_unregister(self, client):
        """ARRANGE: Three students for signup/unregister
           ACT: Sign up multiple, unregister one, verify others remain
           ASSERT: Operations maintain correct participant list"""
        # Arrange
        activity_name = "Chess Club"
        students = ["student1@test.edu", "student2@test.edu", "student3@test.edu"]

        # Act - Sign up all
        for student in students:
            client.post(f"/activities/{activity_name}/signup", params={"email": student})

        # Act - Unregister middle student
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": students[1]}
        )

        # Assert
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        assert students[0] in participants
        assert students[1] not in participants
        assert students[2] in participants
