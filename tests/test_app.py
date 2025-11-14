import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRoot:
    """Test the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Test the activities endpoint"""
    
    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        
    def test_activities_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
            assert isinstance(activity_details["max_participants"], int)


class TestSignupEndpoint:
    """Test the signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "test@example.com" in result["message"]
        assert "Chess Club" in result["message"]
        
    def test_signup_already_registered(self):
        """Test signup for already registered participant"""
        # First signup
        client.post("/activities/Chess%20Club/signup?email=duplicate@example.com")
        
        # Try to signup again
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@example.com"
        )
        assert response.status_code == 400
        
        result = response.json()
        assert "already signed up" in result["detail"]
        
    def test_signup_nonexistent_activity(self):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        
        result = response.json()
        assert "Activity not found" in result["detail"]
        
    def test_signup_updates_participants_list(self):
        """Test that signup updates the participants list"""
        email = "newparticipant@example.com"
        
        # Get initial participants count
        response = client.get("/activities")
        initial_participants = len(response.json()["Math Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Math%20Club/signup?email={email}")
        
        # Check updated participants count
        response = client.get("/activities")
        new_participants = len(response.json()["Math Club"]["participants"])
        
        assert new_participants == initial_participants + 1
        assert email in response.json()["Math Club"]["participants"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregistration"""
        email = "unregister@example.com"
        
        # First signup
        client.post(f"/activities/Soccer%20Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Soccer%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        
    def test_unregister_not_registered(self):
        """Test unregister for participant not in activity"""
        response = client.post(
            "/activities/Swimming%20Team/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        
        result = response.json()
        assert "not signed up" in result["detail"]
        
    def test_unregister_nonexistent_activity(self):
        """Test unregister from activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        
        result = response.json()
        assert "Activity not found" in result["detail"]
        
    def test_unregister_updates_participants_list(self):
        """Test that unregister updates the participants list"""
        email = "tempparticipant@example.com"
        
        # Sign up first
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        # Verify they're registered
        response = client.get("/activities")
        assert email in response.json()["Drama Club"]["participants"]
        
        # Unregister
        client.post(f"/activities/Drama%20Club/unregister?email={email}")
        
        # Verify they're unregistered
        response = client.get("/activities")
        assert email not in response.json()["Drama Club"]["participants"]


class TestActivityIsolation:
    """Test that signup/unregister operations don't affect other activities"""
    
    def test_signup_isolation(self):
        """Test that signing up for one activity doesn't affect others"""
        email = "isolated@example.com"
        
        # Get initial state
        response = client.get("/activities")
        chess_participants_before = len(response.json()["Chess Club"]["participants"])
        programming_participants_before = len(response.json()["Programming Class"]["participants"])
        
        # Sign up for Chess Club
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Check that only Chess Club was affected
        response = client.get("/activities")
        chess_participants_after = len(response.json()["Chess Club"]["participants"])
        programming_participants_after = len(response.json()["Programming Class"]["participants"])
        
        assert chess_participants_after == chess_participants_before + 1
        assert programming_participants_after == programming_participants_before
