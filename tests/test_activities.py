"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    initial_state = {
        "Basketball": {
            "description": "Team sport focusing on skills, strategy, and physical fitness",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Soccer": {
            "description": "Outdoor soccer league for all skill levels",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 22,
            "participants": ["alex@mergington.edu", "sam@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(initial_state)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(initial_state)


class TestGetActivities:
    """Test GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert "Basketball" in data
        assert "Soccer" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """Test that activity details are returned correctly"""
        response = client.get("/activities")
        data = response.json()
        basketball = data["Basketball"]
        
        assert basketball["description"] == "Team sport focusing on skills, strategy, and physical fitness"
        assert basketball["schedule"] == "Mondays and Wednesdays, 4:00 PM - 5:30 PM"
        assert basketball["max_participants"] == 15
        assert "james@mergington.edu" in basketball["participants"]
    
    def test_get_activities_returns_participants(self, client, reset_activities):
        """Test that participants list is included"""
        response = client.get("/activities")
        data = response.json()
        soccer = data["Soccer"]
        
        assert len(soccer["participants"]) == 2
        assert "alex@mergington.edu" in soccer["participants"]
        assert "sam@mergington.edu" in soccer["participants"]


class TestSignupForActivity:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up newstudent@mergington.edu for Basketball"
        
        # Verify participant was added
        assert "newstudent@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signup is prevented"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "james@mergington.edu"}
        )
        assert response.status_code == 400
        assert "Student already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students(self, client, reset_activities):
        """Test multiple students can sign up for same activity"""
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": "student1@mergington.edu"}
        )
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": "student2@mergington.edu"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert "student1@mergington.edu" in activities["Basketball"]["participants"]
        assert "student2@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_signup_activity_full(self, client, reset_activities):
        """Test that signup fails when activity is full"""
        # Fill up Chess Club (max 12, has 2 participants)
        for i in range(10):
            client.post(
                "/activities/Chess Club/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
        
        # This should fail as activity is now full
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overfull@mergington.edu"}
        )
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Test DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from activity"""
        # First verify student is signed up
        assert "james@mergington.edu" in activities["Basketball"]["participants"]
        
        response = client.delete(
            "/activities/Basketball/signup",
            params={"email": "james@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered james@mergington.edu from Basketball" in data["message"]
        
        # Verify participant was removed
        assert "james@mergington.edu" not in activities["Basketball"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from activity that doesn't exist"""
        response = client.delete(
            "/activities/NonexistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_student_not_signed_up(self, client, reset_activities):
        """Test unregister student who is not signed up"""
        response = client.delete(
            "/activities/Basketball/signup",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        assert "Student not signed up for this activity" in response.json()["detail"]
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that student can signup again after unregistering"""
        # Unregister
        response1 = client.delete(
            "/activities/Basketball/signup",
            params={"email": "james@mergington.edu"}
        )
        assert response1.status_code == 200
        assert "james@mergington.edu" not in activities["Basketball"]["participants"]
        
        # Sign up again
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": "james@mergington.edu"}
        )
        assert response2.status_code == 200
        assert "james@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_unregister_frees_up_spot(self, client, reset_activities):
        """Test that unregistering frees up a spot for new signup"""
        # First fill up Chess Club
        for i in range(10):
            client.post(
                "/activities/Chess Club/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
        
        # Try to add one more - should fail
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overfull@mergington.edu"}
        )
        assert response1.status_code == 400
        
        # Unregister one student
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        # Now signup should work
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overfull@mergington.edu"}
        )
        assert response2.status_code == 200


class TestRootEndpoint:
    """Test GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
